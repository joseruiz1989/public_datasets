def create_anot_text(list_paths, folder_dataset, style, json_name="00000_output.json"):
    """
    entra una lista de archivos .png que seran adicionados al dataset
    folder_dataset pasta donde será almazenado el json
    style: estilo de anotacion en los textos
        linear = une los textos de forma directa con diagonales
        med = une los textos en mitad del salto de linea
        min = une los textos para que la mascara sea lo menor posible, pegada al texto
    0: 'text'
    1: 'image'
    2: 'table'
    3: 'equation'
    4: 'title'
    5: 'list'
    """
    assert style in ["linear", "med", "min"]
    data = {}
    final_labels = ['text', 'title', 'list', 'image', 'table', 'equation']
    text_groups = ['text', 'title', 'list', "subtitle", "subsubtitle", "subsubsubtitle",
                "subsubsubsubtitle", "figure_legend", "table_legend", "header", "footer", "numpag"]
    # text_groups = ['text']
    # final_labels = ['title', 'list', 'image', 'table', 'equation']
    labels = []
    for ima, image_path in enumerate(list_paths):
        print(ima+1, "de", len(list_paths), end="\r")
        csv_path = image_path.replace(".png", ".csv")
        # print()
        # print(image_path)
        # print(csv_path)
        basename = os.path.basename(image_path)
        file_name = os.path.splitext(basename)[0]

        file_ref = file_name
        size = ""
        filename = basename
        base64_img_data = ""
        file_attributes = {}
        regions = {}

        df = pd.read_csv(csv_path)
        # print(df.columns)
        counter = 0
        last_label = ""
        last_grouplabel = ""
        repeat = 0
        for index, row in df.iterrows():
            """
            'center_x', 'center_y', 'width', 'height', 'xmin', 'ymin', 'xmax',
            'ymax', 'top_left_x', 'top_left_y', 'top_right_x', 'top_right_y',
            'bottom_right_x', 'bottom_right_y', 'bottom_left_x', 'bottom_left_y',
            'label', 'grouplabel', 'group', 'text_font', 'text_style', 'size_font',
            'filename', 'path', 'filename_mask', 'content'

            'document', 'sub_line_text', 'text', 'title', 'list', 'line', 'image', 'table', 'equation'
            """
            
            x0, y0, x1, y1 = row["xmin"], row["ymin"], row["xmax"], row["ymax"]
            #### arreglar problema de lista antes de terminar subline lista
            if row["label"] == "list" and label == "sub_line_text" and "list_" in row["group"]:
                pass
            else:
            
                label = row["label"]
                grouplabel = row["grouplabel"]
                group = row["group"]
                # if label not in labels:
                    # labels.append(label)

                ### se eh sub_line_text comeca adicionar os pontos, caso seja imagem coloca os pontos diretamente do BB
                if label == "sub_line_text" and grouplabel in text_groups:
                    ### se eh texto que ja foi adicionado na linha anterior, vai adicionando os pontos
                    if last_label == label and last_grouplabel == grouplabel and last_group == group:
                        repeat += 1
                        idx = len(regions)-1
                        x_points = regions[str(idx)]["shape_attributes"]["all_points_x"][:-2*repeat]
                        y_points = regions[str(idx)]["shape_attributes"]["all_points_y"][:-2*repeat]
                        y_median = int((y_points[-1]+y0)/2)

                        x_end = regions[str(idx)]["shape_attributes"]["all_points_x"][-2*repeat:]
                        y_end = regions[str(idx)]["shape_attributes"]["all_points_y"][-2*repeat:]
                        y_median_end = int((y_end[-1]+y1)/2)

                        ### para adicionar os pontos iniciais
                        if style == "linear":
                            x_points.extend([x1, x1, x0, x0])
                            y_points.extend([y0, y1, y1, y0])
                        elif style == "med":
                            x_points.extend([x1, x1, x0, x0])
                            y_points[-1] = y_median
                            y_points.extend([y_median, y1, y1, y_median_end])
                            y_end[0] = y_median_end
                        elif style == "min":
                            if x_points[-1] <= x1: # se a linha de baixo esta na esquerda da de baixo
                                x_points.extend([x1, x1, x0, x0])
                                y_points[-1] = y0
                                y_points.extend([y0, y1, y1, y0])
                            else:
                                x_points.extend([x1, x1, x0, x0])
                                y_points.extend([y_points[-1], y1, y1, y0])


                        ### para adicionar os pontos finais
                        if style == "min":
                            if x_end[0] <= x_points[-1]:   # se a linha encima esta na esquerda da de baixo
                                x_points.extend(x_end)
                                y_points[-1]=y_end[0]
                                y_points.extend(y_end)
                            else:
                                x_points.extend(x_end)
                                y_end[0] = y_points[-1]
                                y_points.extend(y_end)
                        else:
                            x_points.extend(x_end)
                            y_points.extend(y_end)

                        ### reemplaza por os valores novos
                        regions[str(idx)]["shape_attributes"]["all_points_x"] = x_points
                        regions[str(idx)]["shape_attributes"]["all_points_y"] = y_points

                    ### se eh um subline novo, cria uma segmentacao nova
                    else:
                        # print("-----------------------------------------------------")
                        # 0: 'text'
                        # 1: 'image'
                        # 2: 'table'
                        # 3: 'equation'
                        # 4: 'title'
                        # 5: 'list'

                        repeat = 0
                        if grouplabel == 'text': element_class = 0
                        elif grouplabel == 'figure_legend': element_class = 0
                        elif grouplabel == 'table_legend': element_class = 0
                        elif grouplabel == 'header': element_class = 0
                        elif grouplabel == 'footer': element_class = 0
                        elif grouplabel == 'numpag': element_class = 0

                        elif grouplabel == 'image': element_class = 1
                        elif grouplabel == 'table': element_class = 2
                        elif grouplabel == 'equation': element_class = 3
                        
                        elif grouplabel == 'title': element_class = 4
                        elif grouplabel == 'subtitle': element_class = 4
                        elif grouplabel == 'subsubtitle': element_class = 4
                        elif grouplabel == 'subsubsubtitle': element_class = 4

                        elif grouplabel == 'list': element_class = 5
                        else:
                            print("classe nao existe")
                            break
                        shape_attributes = {"name": "polygon",
                                            "all_points_x" : [x0, x1, x1, x0, x0],
                                            "all_points_y" : [y0, y0, y1, y1, y0],
                                            "element_class": element_class
                                            }
                        region_attributes = {}
                        regions[str(counter)] = {"shape_attributes" : shape_attributes,
                                                "region_attributes" : region_attributes
                                                }
                        # print(label, x0, y0, x1, y1)
                        counter += 1
                ### se eh imagem, cria direitamente os BB
                # 0: 'text'
                # 1: 'image'
                # 2: 'table'
                # 3: 'equation'
                # 4: 'title'
                # 5: 'list'
                elif label == 'image' or label == 'table' or label == 'equation':
                    if label == 'sub_line_text': element_class = 0
                    elif label == 'image': element_class = 1
                    elif label == 'table': element_class = 2
                    elif label == 'equation': element_class = 3
                    elif label == 'title': element_class = 4
                    elif label == 'list': element_class = 5
                    else:
                        print("classe nao existe")
                        break
                    shape_attributes = {"name": "polygon",
                                        "all_points_x" : [x0, x1, x1, x0, x0],
                                        "all_points_y" : [y0, y0, y1, y1, y0],
                                        "element_class": element_class
                                        }
                    region_attributes = {}
                    regions[str(counter)] = {"shape_attributes" : shape_attributes,
                                            "region_attributes" : region_attributes
                                            }
                    # print(label, x0, y0, x1, y1)
                    counter += 1


                last_label = row["label"]
                last_grouplabel = row["grouplabel"]
                last_group = row["group"]

        data[file_name] = {"file_ref": file_ref,
                        "size": size,
                        "filename": filename,
                        "base64_img_data": base64_img_data,
                        "file_attributes": file_attributes,
                        "regions": regions
        }

    print(ima+1, "de", len(list_paths))
    json_path = folder_dataset + json_name
    with open(json_path, "w") as outfile:
        json.dump(data, outfile)



def get_document_dicts(img_dir, json_file):
    json_file = os.path.join(img_dir, json_file)
    with open(json_file) as f:
        imgs_anns = json.load(f)

    dataset_dicts = []
    for idx, v in enumerate(imgs_anns.values()):
        record = {}
        
        filename = os.path.join(img_dir, v["filename"])
        height, width = cv2.imread(filename).shape[:2]
        
        record["file_name"] = filename
        record["image_id"] = idx
        record["height"] = height
        record["width"] = width
      
        annos = v["regions"]
        objs = []
        for _, anno in annos.items():
            assert not anno["region_attributes"]
            anno = anno["shape_attributes"]
            px = anno["all_points_x"]
            py = anno["all_points_y"]
            poly = [(x + 0.5, y + 0.5) for x, y in zip(px, py)]
            poly = [p for x in poly for p in x]
            element_class = anno["element_class"]

            obj = {
                "bbox": [np.min(px), np.min(py), np.max(px), np.max(py)],
                "bbox_mode": BoxMode.XYXY_ABS,
                "segmentation": [poly],
                "category_id": element_class,
            }
            objs.append(obj)
        record["annotations"] = objs
        dataset_dicts.append(record)
    return dataset_dicts