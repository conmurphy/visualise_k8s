'''
Copyright (c) 2019 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.0 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
'''

from kubernetes import client, config
from kubernetes.client import configuration
from pick import pick
import json
import webbrowser, os


def main():
    contexts, active_context = config.list_kube_config_contexts()
    if not contexts:
        print("Cannot find any context in kube-config file.")
        return
    contexts = [context['name'] for context in contexts]
    active_index = contexts.index(active_context['name'])
    clusterName, _ = pick(contexts, title="Pick the context to load", default_index=active_index)

    config.load_kube_config(context=clusterName)

    all_rows = []
    new_row = {}

    appsV1Beta2Api = client.AppsV1beta2Api()
    coreV1Api = client.CoreV1Api()
    networkingV1Api = client.NetworkingV1Api()
    networkingV1beta1Api = client.NetworkingV1beta1Api()
    extensionsV1beta1Api = client.ExtensionsV1beta1Api()

    api_response = coreV1Api.list_namespace(watch=False, _preload_content=False)

    api_response = json.loads(api_response.data)
    namespaces = api_response["items"]

    api_response = coreV1Api.list_endpoints_for_all_namespaces(watch=False, _preload_content=False)

    api_response = json.loads(api_response.data)
    endpoints = api_response["items"]

    api_response = extensionsV1beta1Api.list_ingress_for_all_namespaces(watch=False, _preload_content=False)

    api_response = json.loads(api_response.data)
    ingresses = api_response["items"]

    for namespace in namespaces:
        ingress_row = { 'kind': 'Ingress', 'name': "missing" ,'className': 'missing','children': []}
        new_row = {"kind": "Namespace" , "name": namespace["metadata"]["name"], "className": "namespace", "children": []}
        new_row["children"].append(ingress_row)
        all_rows.append(new_row)

    
    
    for ingress in ingresses:
        namespace = ingress["metadata"]["namespace"]

        for idx, item in enumerate(all_rows):
            if item["className"] == "namespace" and item["name"] == namespace:
                if ingress["metadata"]["name"] not in [x['name'] for x in item["children"]]:
                    new_row = { 'kind': 'Ingress', 'name': ingress["metadata"]["name"], 'className': 'ingress','children': []}
                    item["children"].append(new_row)

        for rule in ingress["spec"]["rules"]:
            for service in rule["http"]["paths"]:
                serviceName = service["backend"]["serviceName"]
                path = service["path"]

                for namespace_idx, namespace_item in enumerate(all_rows):
                    if namespace_item["className"] == "namespace" and namespace_item["name"] == namespace:
                        for ingress_idx, ingress_item in enumerate(all_rows[namespace_idx]["children"]):
                            if ingress_item["className"] == "ingress" and ingress_item["name"] == ingress["metadata"]["name"]:
                                if serviceName not in [x['name'] for x in ingress_item["children"]]:
                                    new_row = { 'kind': 'Service', 'name': serviceName, 'ingressPath': path,'className': 'service','children': []}
                                    ingress_item["children"].append(new_row)
            

    '''
        The endpoints response contains namespace, services name, pod name, node name and endpoint IP so we 
        will parse all endpoints and add them to the required structure for the org chart
    '''

    for endpoint in endpoints:
        namespace = endpoint["metadata"]["namespace"]

        if namespace not in [x['name'] for x in all_rows]:
            new_row = { 'kind': 'Namespace', 'name': namespace, 'className': 'namespace','children': []}
            all_rows.append(new_row)

        serviceName = endpoint["metadata"]["name"]

        missing_ingress_idx = 0 
        ingress_missing = True

        for namespace_idx, namespace_item in enumerate(all_rows):
            if namespace_item["className"] == "namespace" and namespace_item["name"] == namespace:
                for ingress_idx, ingress_item in enumerate(all_rows[namespace_idx]["children"]):
                    for service_idx, service_item in enumerate(all_rows[namespace_idx]["children"][ingress_idx]["children"]):
                        if serviceName in service_item["name"]:
                            ingress_missing = False
                            if "subsets" in endpoint:
                                for subset in endpoint["subsets"]:
                                    for address in subset["addresses"]:
                                        if "ip" in address:
                                            ip = address["ip"]
                                        if "nodeName" in address:
                                            nodeName = address["nodeName"]
                                        if "targetRef" in address:
                                            podName = address["targetRef"]["name"]

                                        new_row = { 'kind': 'Pod', 'name': podName, 'node': nodeName,'ip':ip ,"className":"pod"}
                                        service_item["children"].append(new_row)
            
            
                # No ingress was found with this service name so add it to the  "Missing" ingress which will be invisible
                if ingress_missing:
                    if serviceName not in [x['name'] for x in all_rows[namespace_idx]["children"][missing_ingress_idx]["children"]]:
                        pod_row = {}
                        if "subsets" in endpoint:
                            for subset in endpoint["subsets"]:
                                for address in subset["addresses"]:
                                    if "ip" in address:
                                        ip = address["ip"]
                                    if "nodeName" in address:
                                        nodeName = address["nodeName"]
                                    if "targetRef" in address:
                                        podName = address["targetRef"]["name"]

                                    pod_row = { 'kind': 'Pod', 'name': podName, 'node': nodeName,'ip':ip ,"className":"pod"}
                                    
                        new_row = { 'kind': 'Service', 'name': serviceName, 'className': 'service','children': []}
                        new_row["children"].append(pod_row)
                        all_rows[namespace_idx]["children"][missing_ingress_idx]["children"].append(new_row)

    cluster_row = {"kind": "K8s Cluster","name": clusterName, "children": all_rows}

    final_output = "var datasource = {};".format(cluster_row)
    
    with open("assets/data/k8s_data.js", "w") as out:
        out.write(final_output) 
    
    webbrowser.open('file://' + os.path.realpath("index.html"))

if __name__ == '__main__':
    main()