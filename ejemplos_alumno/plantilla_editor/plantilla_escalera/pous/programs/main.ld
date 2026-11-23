PROGRAM main
  VAR
    entrada AT %IX0.1 : BOOL;
    salida AT %QX0.1 : BOOL;
  END_VAR

{
  "name": "main",
  "rungs": [
    {
      "id": "rung_main_plantilla-0001",
      "comment": "La salida sigue a la entrada",
      "defaultBounds": [
        300,
        100
      ],
      "reactFlowViewport": [
        303,
        120
      ],
      "nodes": [
        {
          "id": "left-rail-rung_main_plantilla-0001",
          "type": "powerRail",
          "position": {
            "x": 0,
            "y": 30
          },
          "data": {
            "handles": [
              {
                "id": "left-rail",
                "position": "right",
                "type": "source",
                "isConnectable": false,
                "glbPosition": {
                  "x": 3,
                  "y": 50
                },
                "relPosition": {
                  "x": 3,
                  "y": 20
                },
                "style": {
                  "top": 20,
                  "right": -3
                }
              }
            ],
            "inputHandles": [],
            "outputHandles": [
              {
                "id": "left-rail",
                "position": "right",
                "type": "source",
                "isConnectable": false,
                "glbPosition": {
                  "x": 3,
                  "y": 50
                },
                "relPosition": {
                  "x": 3,
                  "y": 20
                },
                "style": {
                  "top": 20,
                  "right": -3
                }
              }
            ],
            "inputConnector": null,
            "outputConnector": {
              "id": "left-rail",
              "position": "right",
              "type": "source",
              "isConnectable": false,
              "glbPosition": {
                "x": 3,
                "y": 50
              },
              "relPosition": {
                "x": 3,
                "y": 20
              },
              "style": {
                "top": 20,
                "right": -3
              }
            },
            "numericId": "1000001",
            "variant": "left",
            "variable": {
              "name": ""
            },
            "executionOrder": 0,
            "draggable": false,
            "selectable": false,
            "deletable": false
          },
          "width": 3,
          "height": 40,
          "measured": {
            "width": 3,
            "height": 40
          },
          "draggable": false,
          "selectable": false,
          "selected": false,
          "dragging": false
        },
        {
          "id": "right-rail-rung_main_plantilla-0001",
          "type": "powerRail",
          "position": {
            "x": 300,
            "y": 30
          },
          "data": {
            "handles": [
              {
                "id": "right-rail",
                "position": "left",
                "type": "target",
                "isConnectable": false,
                "glbPosition": {
                  "x": 297,
                  "y": 50
                },
                "relPosition": {
                  "x": 3,
                  "y": 20
                },
                "style": {
                  "top": 20,
                  "left": -3
                }
              }
            ],
            "inputHandles": [
              {
                "id": "right-rail",
                "position": "left",
                "type": "target",
                "isConnectable": false,
                "glbPosition": {
                  "x": 297,
                  "y": 50
                },
                "relPosition": {
                  "x": 3,
                  "y": 20
                },
                "style": {
                  "top": 20,
                  "left": -3
                }
              }
            ],
            "outputHandles": [],
            "inputConnector": {
              "id": "right-rail",
              "position": "left",
              "type": "target",
              "isConnectable": false,
              "glbPosition": {
                "x": 297,
                "y": 50
              },
              "relPosition": {
                "x": 3,
                "y": 20
              },
              "style": {
                "top": 20,
                "left": -3
              }
            },
            "outputConnector": null,
            "numericId": "1000002",
            "variant": "right",
            "variable": {
              "name": ""
            },
            "executionOrder": 0,
            "draggable": false,
            "selectable": false,
            "deletable": false
          },
          "width": 3,
          "height": 40,
          "measured": {
            "width": 3,
            "height": 40
          },
          "draggable": false,
          "selectable": false,
          "selected": false,
          "dragging": false
        },
        {
          "id": "CONTACT_plantilla_0001",
          "type": "contact",
          "position": {
            "x": 110,
            "y": 38
          },
          "data": {
            "handles": [
              {
                "id": "input",
                "position": "left",
                "type": "target",
                "isConnectable": false,
                "glbPosition": {
                  "x": 110,
                  "y": 38
                },
                "relPosition": {
                  "x": 0,
                  "y": 12
                },
                "style": {
                  "left": -3
                }
              },
              {
                "id": "output",
                "position": "right",
                "type": "source",
                "isConnectable": false,
                "glbPosition": {
                  "x": 134,
                  "y": 38
                },
                "relPosition": {
                  "x": 24,
                  "y": 12
                },
                "style": {
                  "right": -3
                }
              }
            ],
            "variant": "default",
            "inputHandles": [
              {
                "id": "input",
                "position": "left",
                "type": "target",
                "isConnectable": false,
                "glbPosition": {
                  "x": 110,
                  "y": 38
                },
                "relPosition": {
                  "x": 0,
                  "y": 12
                },
                "style": {
                  "left": -3
                }
              }
            ],
            "outputHandles": [
              {
                "id": "output",
                "position": "right",
                "type": "source",
                "isConnectable": false,
                "glbPosition": {
                  "x": 134,
                  "y": 38
                },
                "relPosition": {
                  "x": 24,
                  "y": 12
                },
                "style": {
                  "right": -3
                }
              }
            ],
            "inputConnector": {
              "id": "input",
              "position": "left",
              "type": "target",
              "isConnectable": false,
              "glbPosition": {
                "x": 110,
                "y": 38
              },
              "relPosition": {
                "x": 0,
                "y": 12
              },
              "style": {
                "left": -3
              }
            },
            "outputConnector": {
              "id": "output",
              "position": "right",
              "type": "source",
              "isConnectable": false,
              "glbPosition": {
                "x": 134,
                "y": 38
              },
              "relPosition": {
                "x": 24,
                "y": 12
              },
              "style": {
                "right": -3
              }
            },
            "numericId": "2000001",
            "variable": {
              "name": "entrada"
            },
            "executionOrder": 0,
            "draggable": true,
            "selectable": true,
            "deletable": true
          },
          "width": 24,
          "height": 24,
          "measured": {
            "width": 24,
            "height": 24
          },
          "draggable": true,
          "selectable": true,
          "selected": false,
          "dragging": false
        },
        {
          "id": "COIL_plantilla_0001",
          "type": "coil",
          "position": {
            "x": 170,
            "y": 38
          },
          "data": {
            "handles": [
              {
                "id": "input",
                "position": "left",
                "type": "target",
                "isConnectable": false,
                "glbPosition": {
                  "x": 170,
                  "y": 38
                },
                "relPosition": {
                  "x": 0,
                  "y": 12
                },
                "style": {
                  "left": -3
                }
              },
              {
                "id": "output",
                "position": "right",
                "type": "source",
                "isConnectable": false,
                "glbPosition": {
                  "x": 198,
                  "y": 38
                },
                "relPosition": {
                  "x": 28,
                  "y": 12
                },
                "style": {
                  "right": -3
                }
              }
            ],
            "variant": "default",
            "inputHandles": [
              {
                "id": "input",
                "position": "left",
                "type": "target",
                "isConnectable": false,
                "glbPosition": {
                  "x": 170,
                  "y": 38
                },
                "relPosition": {
                  "x": 0,
                  "y": 12
                },
                "style": {
                  "left": -3
                }
              }
            ],
            "outputHandles": [
              {
                "id": "output",
                "position": "right",
                "type": "source",
                "isConnectable": false,
                "glbPosition": {
                  "x": 198,
                  "y": 38
                },
                "relPosition": {
                  "x": 28,
                  "y": 12
                },
                "style": {
                  "right": -3
                }
              }
            ],
            "inputConnector": {
              "id": "input",
              "position": "left",
              "type": "target",
              "isConnectable": false,
              "glbPosition": {
                "x": 170,
                "y": 38
              },
              "relPosition": {
                "x": 0,
                "y": 12
              },
              "style": {
                "left": -3
              }
            },
            "outputConnector": {
              "id": "output",
              "position": "right",
              "type": "source",
              "isConnectable": false,
              "glbPosition": {
                "x": 198,
                "y": 38
              },
              "relPosition": {
                "x": 28,
                "y": 12
              },
              "style": {
                "right": -3
              }
            },
            "numericId": "2000002",
            "variable": {
              "name": "salida"
            },
            "executionOrder": 1,
            "draggable": true,
            "selectable": true,
            "deletable": true
          },
          "width": 28,
          "height": 24,
          "measured": {
            "width": 28,
            "height": 24
          },
          "draggable": true,
          "selectable": true,
          "selected": false,
          "dragging": false
        }
      ],
      "edges": [
        {
          "id": "e_left-rail-rung_main_plantilla-0001_CONTACT_plantilla_0001__left-rail_input",
          "source": "left-rail-rung_main_plantilla-0001",
          "target": "CONTACT_plantilla_0001",
          "sourceHandle": "left-rail",
          "targetHandle": "input",
          "type": "smoothstep"
        },
        {
          "id": "e_CONTACT_plantilla_0001_COIL_plantilla_0001__output_input",
          "source": "CONTACT_plantilla_0001",
          "target": "COIL_plantilla_0001",
          "sourceHandle": "output",
          "targetHandle": "input",
          "type": "smoothstep"
        },
        {
          "id": "e_COIL_plantilla_0001_right-rail-rung_main_plantilla-0001__output_right-rail",
          "source": "COIL_plantilla_0001",
          "target": "right-rail-rung_main_plantilla-0001",
          "sourceHandle": "output",
          "targetHandle": "right-rail",
          "type": "smoothstep"
        }
      ],
      "selectedNodes": []
    }
  ]
}
END_PROGRAM