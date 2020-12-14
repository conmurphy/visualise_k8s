/*
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
*/

$(function() {

    var nodeTemplate = function(data) {
        return `
            <div class="title">${data.kind}</div>
            <div class="content">${data.name}</div>
        `;        
    };

    var oc = $('#chart-container').orgchart({
        'data' : datasource,
        'direction': 'l2r',
        'zoom': false,
        'pan': true,
        'nodeTemplate': nodeTemplate,
        'nodeContent': 'title',
        'createNode': function($node, data) {

            if (data["className"] == "pod"){
                var secondMenuIcon = $('<i>', {
                    'class': 'fa fa-info-circle my-square second-menu-icon',
                    click: function() {
                        $(this).siblings('.second-menu').toggle();
                    }
                });
                    
                infoPanel=""

                if (data.className == "pod"){

                    infoPanel += "<div>IP Address: "+ data["ip"] +"</div>"
                    infoPanel += "<div>Node: "+ data["node"] +"</div>"

                }
                    
                    
                var secondMenu = '<div class="second-menu">'+ infoPanel +'</div>';
                    $node.append(secondMenuIcon).append(secondMenu);
            };

            if (data["className"] == "service" && "ingressPath" in data ){
                var secondMenuIcon = $('<i>', {
                    'class': 'fa fa-info-circle my-square second-menu-icon',
                    click: function() {
                        $(this).siblings('.second-menu').toggle();
                    }
                });
                

                infoPanel=""

                if (data.className == "service"){
                    infoPanel += "<div>Ingress Path: "+ data["ingressPath"] +"</div>"
                }
                    
                    
                var secondMenu = '<div class="second-menu">'+ infoPanel +'</div>';
                    $node.append(secondMenuIcon).append(secondMenu);
            }
    }

});


});