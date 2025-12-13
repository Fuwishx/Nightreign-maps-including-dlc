import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os

def generate_maps_from_csv(csv_file, materials_folder, coordinates_file, construct_file, name_file, output_folder, font_path=None):
    """
    根据CSV文件批量生成建筑分布图
    """
    
    os.makedirs(output_folder, exist_ok=True)
    
    print("读取数据CSV文件...")
    data_df = pd.read_csv(csv_file)
    
    print("读取坐标CSV文件...")
    coord_df = pd.read_csv(coordinates_file)
    coord_dict = {}
    for _, row in coord_df.iterrows():
        index_val = row.iloc[0]
        x_coord = row.iloc[7]
        y_coord = row.iloc[8]
        coord_dict[index_val] = (x_coord, y_coord)
    
    print("读取建筑信息CSV文件...")
    construct_df = pd.read_csv(construct_file)
    
    # 读取名称映射文件
    print("读取名称映射文件...")
    name_df = pd.read_csv(name_file,header=None)
    name_dict = {}
    for _, row in name_df.iterrows():
        name_dict[row.iloc[0]] = row.iloc[1]
    
    # 创建两个字典，分别存储特殊建筑和普通建筑
    special_construct_dict = {}  # 49410/49420/49430
    normal_construct_dict = {}   # 其他建筑

    # 大空洞底层建筑坐标    
    underground_coords = {1160, 1159, 1107, 1110, 1153, 1175, 1174, 1213}

    # 大空洞神授塔BOSS坐标
    floor_prefix = {
        1111: "1F ",
        1112: "2F ",
        1113: "3F ",
        1114: "1F ",
        1115: "2F ",
        1116: "3F ",
    }
    # 大空洞全建筑坐标变换
    def transform_coord(x, y, coord_index):
        # 基础放大（101.86%）
        x = x * 1.0186
        y = y * 1.0186

        # 基础平移（非地底 & 地底都要）
        x -= 306
        y -= 260

        # 若为地底建筑，继续右 +862，下 +355
        if coord_index in underground_coords:
            x += 862
            y += 355

        return x, y


    
    for _, construct_row in construct_df.iterrows():
        map_id = construct_row.iloc[1]
        show_flag = construct_row.iloc[3]
        
        if show_flag == 1:
            construct_type = construct_row.iloc[2]
            coord_index = construct_row.iloc[4]
            
            # 检查是否为特殊建筑
            if construct_type in [49410, 49420, 49430]:
                if map_id not in special_construct_dict:
                    special_construct_dict[map_id] = []
                special_construct_dict[map_id].append({
                    'type': construct_type,
                    'coord_index': coord_index
                })
            else:
                if map_id not in normal_construct_dict:
                    normal_construct_dict[map_id] = []
                normal_construct_dict[map_id].append({
                    'type': construct_type,
                    'coord_index': coord_index
                })
    
    # 修改字体加载部分，创建三种不同大小的字体
    font_event = None
    font_night = None
    font_building = None
    font_floor = None
    
    if font_path and os.path.exists(font_path):
        try:
            font_event = ImageFont.truetype("AiDianGanFengXingKai-2.ttf", 160)  # 特殊事件标注字体
            font_night = ImageFont.truetype("SmileySans-Oblique.ttf", 95)  # night_circle标注字体
            font_building = ImageFont.truetype("SmileySans-Oblique.ttf", 65)  # 建筑标注字体
            font_floor = ImageFont.truetype("SmileySans-Oblique.ttf", 90)  # 建筑标注字体
            print(f"成功加载字体: {font_path}")
        except Exception as e:
            font_event = ImageFont.load_default()
            font_night = ImageFont.load_default()
            font_building = ImageFont.load_default()
            print(f"无法加载指定字体 {font_path}，使用默认字体: {e}")
    else:
        font_event = ImageFont.load_default()
        font_night = ImageFont.load_default()
        font_building = ImageFont.load_default()
        print("使用默认字体")
    
    night_circle_path = os.path.join(materials_folder, "night_circle.png")
    if not os.path.exists(night_circle_path):
        print(f"错误: night_circle素材不存在 {night_circle_path}")
        return
    
    try:
        night_circle_img = Image.open(night_circle_path).convert('RGBA')
    except:
        print(f"错误: 无法加载night_circle素材 {night_circle_path}")
        return
    
    print("开始生成图片...")
    for idx, row in data_df.iterrows():
        # 调试用-跳过前 435 行
        if idx < 435:
            continue

        # 调试用-缩放倍数，
        tran = 5

        ID = row["ID"]
        special_value = row['Special']
        
        # 调试用-只生成大空洞
        if special_value != 4:
            continue
        
        background_path = os.path.join(materials_folder, f"background_{special_value}.png")
        
        if not os.path.exists(background_path):
            print(f"警告: 背景图片不存在 {background_path}，跳过此行")
            continue
            
        try:
            background = Image.open(background_path).convert('RGBA')
        except:
            print(f"错误: 无法加载背景图片 {background_path}，跳过此行")
            continue
            
        draw = ImageDraw.Draw(background)
        
        # 检查特殊事件 - 修正列引用（使用第9列EvPatFlag）
        event_value = row['Event_30*0']        
        event_flag = row['EventFlag']
        if event_flag == 7707 or event_flag == 7727:
            evpat_value = row['EvPatFlag']  # 第9列
            frenzy_path = os.path.join(materials_folder, f"Frenzy_{evpat_value}.png")
            if os.path.exists(frenzy_path):
                try:
                    frenzy_img = Image.open(frenzy_path).convert('RGBA')
                    # 使用paste方式叠加特殊事件素材
                    background.paste(frenzy_img, (0, 0), frenzy_img)
                    # 重新创建draw对象
                    draw = ImageDraw.Draw(background)
                except Exception as e:
                    print(f"错误: 无法处理Frenzy素材 {frenzy_path}: {e}")
            else:
                print(f"警告: Frenzy素材不存在 {frenzy_path}")
        
        # 添加NightLord素材 - 使用alpha_composite正确处理透明度
        nightlord_value = row['NightLord']
        nightlord_path = os.path.join(materials_folder, f"nightlord_{nightlord_value}.png")
        if os.path.exists(nightlord_path):
            try:
                nightlord_img = Image.open(nightlord_path).convert('RGBA')
                # 使用alpha_composite而不是paste
                background = Image.alpha_composite(background, nightlord_img)
                # 重新创建draw对象
                draw = ImageDraw.Draw(background)
            except Exception as e:
                print(f"错误: 无法处理NightLord素材 {nightlord_path}: {e}")
        else:
            print(f"警告: NightLord素材不存在 {nightlord_path}")
        
        # 添加Treasure素材 - 使用alpha_composite
        treasure_value = row['Treasure_800']
        combined_value = treasure_value * 10 + special_value
        treasure_path = os.path.join(materials_folder, f"treasure_{combined_value}.png")
        if os.path.exists(treasure_path):
            try:
                treasure_img = Image.open(treasure_path).convert('RGBA')
                # 使用alpha_composite而不是paste
                background = Image.alpha_composite(background, treasure_img)
                # 重新创建draw对象
                draw = ImageDraw.Draw(background)
            except Exception as e:
                print(f"错误: 无法处理Treasure素材 {treasure_path}: {e}")
        else:
            print(f"警告: Treasure素材不存在 {treasure_path}")

        # === 添加 day2_x.png 额外素材（仅 special_value == 4 时） ===
        if special_value == 4:
            x = row['Day2Loc']
            extra_day2_path = os.path.join(materials_folder, f"day2_{x}.png")
            if os.path.exists(extra_day2_path):
                try:
                    extra_day2_img = Image.open(extra_day2_path).convert('RGBA')
                    # 叠加在背景之上，但在所有图标与文字之下
                    background = Image.alpha_composite(background, extra_day2_img)
                    draw = ImageDraw.Draw(background)
                except Exception as e:
                    print(f"错误: 无法处理 day2_{x}.png 素材: {e}")
            else:
                print(f"警告: day2_{x}.png 不存在于素材目录")

        
        # 添加RotRew_500素材 - 仅在值不为0时添加
        rotrew_value = row['RotRew_500']
        if rotrew_value != 0:  # 只在值不为0时处理
            rotrew_path = os.path.join(materials_folder, f"RotRew_{rotrew_value}.png")
            if os.path.exists(rotrew_path):
                try:
                    rotrew_img = Image.open(rotrew_path).convert('RGBA')
                    # 使用alpha_composite合并图层
                    background = Image.alpha_composite(background, rotrew_img)
                    # 重新创建draw对象
                    draw = ImageDraw.Draw(background)
                except Exception as e:
                    print(f"错误: 无法处理RotRew素材 {rotrew_path}: {e}")
            else:
                print(f"警告: RotRew素材不存在 {rotrew_path}")
        
        # 添加night_circle素材 - 使用paste方式
        day1_loc = row['Day1Loc']
        day1_boss = row['Day1Boss']
        day1_extra = row.iloc[14] if len(row) > 14 else -1  # 第15列
        
        day2_loc = row['Day2Loc']
        day2_boss = row['Day2Boss']
        day2_extra = row.iloc[15] if len(row) > 15 else -1  # 第16列
        
        # 存储night_circle文字信息，稍后绘制
        night_circle_texts = []
        
        if day1_loc in coord_dict:
            x, y = coord_dict[day1_loc]
            
            # 大空洞建筑平移
            if special_value == 4:
                x, y = transform_coord(x, y, day1_loc)
                
            x_pos = int(round(x - night_circle_img.width // 2))
            y_pos = int(round(y - night_circle_img.height // 2))
            # 使用paste方式叠加
            background.paste(night_circle_img, (x_pos, y_pos), night_circle_img)
            
            # 存储night_circle标识文字信息
            if day1_boss in name_dict:
                text = "DAY1 "+name_dict[day1_boss]
                # 使用getbbox替代textsize
                bbox = font_night.getbbox(text)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                text_x = int(round(x - text_width // 2))
                text_y = int(round(y - text_height // 2))
                
                night_circle_texts.append({
                    'text': text,
                    'position': (text_x, text_y),
                    'font': font_night
                })
                
                # 存储额外文字（第15列）
                if day1_extra != -1 and day1_extra in name_dict:
                    extra_text = name_dict[day1_extra]
                    bbox_extra = font_night.getbbox(extra_text)
                    extra_width = bbox_extra[2] - bbox_extra[0]
                    extra_height = bbox_extra[3] - bbox_extra[1]
                    extra_x = int(round(x - extra_width // 2))
                    extra_y = int(round(text_y + text_height + 5))  # 在主文字下方
                    
                    night_circle_texts.append({
                        'text': extra_text,
                        'position': (extra_x, extra_y),
                        'font': font_night
                    })
        else:
            print(f"警告: 坐标 {day1_loc} 在坐标文件中不存在")
        
        if day2_loc in coord_dict:
            x, y = coord_dict[day2_loc]
            
            # 大空洞建筑平移
            if special_value == 4:
                x, y = transform_coord(x, y, day2_loc)

            x_pos = int(round(x - night_circle_img.width // 2))
            y_pos = int(round(y - night_circle_img.height // 2))
            # 使用paste方式叠加
            background.paste(night_circle_img, (x_pos, y_pos), night_circle_img)
            
            # 存储night_circle标识文字信息
            if day2_boss in name_dict:
                text = "DAY2 "+name_dict[day2_boss]
                # 使用getbbox替代textsize
                bbox = font_night.getbbox(text)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                text_x = int(round(x - text_width // 2))
                text_y = int(round(y - text_height // 2))
                
                night_circle_texts.append({
                    'text': text,
                    'position': (text_x, text_y),
                    'font': font_night
                })
                
                # 存储额外文字（第16列）
                if day2_extra != -1 and day2_extra in name_dict:
                    extra_text = name_dict[day2_extra]
                    bbox_extra = font_night.getbbox(extra_text)
                    extra_width = bbox_extra[2] - bbox_extra[0]
                    extra_height = bbox_extra[3] - bbox_extra[1]
                    extra_x = int(round(x - extra_width // 2))
                    extra_y = int(round(text_y + text_height + 5))  # 在主文字下方
                    
                    night_circle_texts.append({
                        'text': extra_text,
                        'position': (extra_x, extra_y),
                        'font': font_night
                    })
        else:
            print(f"警告: 坐标 {day2_loc} 在坐标文件中不存在")
        
        # 添加建筑素材 - 先添加特殊建筑(49410/49420/49430)
        current_map_id = row['ID']
        
        # 存储建筑文字信息，稍后绘制
        building_texts = []
        floor_texts = []
        
        # 添加特殊建筑
        if current_map_id in special_construct_dict:
            for construct_info in special_construct_dict[current_map_id]:
                construct_type = construct_info['type']
                coord_index = construct_info['coord_index']
                
                if coord_index in coord_dict:
                    x, y = coord_dict[coord_index]
                    
                    # 大空洞建筑平移
                    if special_value == 4:
                        x, y = transform_coord(x, y, coord_index)

                    
                    construct_path = os.path.join(materials_folder, f"Construct_{construct_type}.png")
                    if os.path.exists(construct_path):
                        try:
                            construct_img = Image.open(construct_path).convert('RGBA')
                            # 计算位置，使建筑素材中心位于坐标点
                            x_pos = int(round(x - construct_img.width // 2))
                            y_pos = int(round(y - construct_img.height // 2))
                            # 使用paste叠加
                            background.paste(construct_img, (x_pos, y_pos), construct_img)
                            
                            # 存储建筑标识文字信息
                            if construct_type in name_dict:
                                text = name_dict[construct_type]
                                # 使用getbbox替代textsize
                                bbox = font_building.getbbox(text)
                                text_width = bbox[2] - bbox[0]
                                text_height = bbox[3] - bbox[1]
                                text_x = int(round(x - text_width // 2))
                                text_y = int(round(y + construct_img.height // 2 + 10))  # 在建筑下方
                                
                                building_texts.append({
                                    'text': text,
                                    'position': (text_x, text_y),
                                    'font': font_building
                                })
                        except Exception as e:
                            print(f"错误: 无法处理建筑素材 {construct_path}: {e}")
                    else:
                        print(f"警告: 建筑素材不存在 {construct_path}")
                else:
                    print(f"警告: 坐标索引 {coord_index} 在坐标文件中不存在")
        
        # 添加普通建筑
        if current_map_id in normal_construct_dict:
            for construct_info in normal_construct_dict[current_map_id]:
                construct_type = construct_info['type']
                coord_index = construct_info['coord_index']
                
                if coord_index in coord_dict:
                    x, y = coord_dict[coord_index]
                    
                    # 大空洞建筑平移
                    if special_value == 4:
                        x, y = transform_coord(x, y, coord_index)

                    # 大空洞神授塔单独处理
                    if coord_index in floor_prefix:
                        text = floor_prefix[coord_index] + name_dict[construct_type]
                        # 使用getbbox替代textsize
                        bbox = font_building.getbbox(text)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                        text_x = int(round(x - text_width // 2))
                        text_y = int(round(y - text_height // 2))  # 在建筑下方
                        
                        floor_texts.append({
                            'text': text,
                            'position': (text_x, text_y),
                            'font': font_floor
                        })
                        continue
                    
                    construct_path = os.path.join(materials_folder, f"Construct_{construct_type}.png")
                    if os.path.exists(construct_path):
                        try:
                            construct_img = Image.open(construct_path).convert('RGBA')
                            # 计算位置，使建筑素材中心位于坐标点
                            x_pos = int(round(x - construct_img.width // 2))
                            y_pos = int(round(y - construct_img.height // 2))
                            # 使用paste叠加
                            background.paste(construct_img, (x_pos, y_pos), construct_img)
                            
                            # 存储建筑标识文字信息
                            if construct_type in name_dict:
                                text = name_dict[construct_type]
                                
                                # 使用getbbox替代textsize
                                bbox = font_building.getbbox(text)
                                text_width = bbox[2] - bbox[0]
                                text_height = bbox[3] - bbox[1]
                                text_x = int(round(x - text_width // 2))
                                text_y = int(round(y + construct_img.height // 2 + 10))  # 在建筑下方
                                
                                building_texts.append({
                                    'text': text,
                                    'position': (text_x, text_y),
                                    'font': font_building
                                })
                        except Exception as e:
                            print(f"错误: 无法处理建筑素材 {construct_path}: {e}")
                    else:
                        print(f"警告: 建筑素材不存在 {construct_path}")
                else:
                    print(f"警告: 坐标索引 {coord_index} 在坐标文件中不存在")
        
        # 添加Start素材 - 确保在最上层
        start_value = row['Start_190']
        start_path = os.path.join(materials_folder, f"Start_{start_value}.png")
        if os.path.exists(start_path):
            try:
                start_img = Image.open(start_path).convert('RGBA')
                # 使用alpha_composite而不是paste
                background = Image.alpha_composite(background, start_img)
                # 重新创建draw对象
                draw = ImageDraw.Draw(background)
            except Exception as e:
                print(f"错误: 无法处理Start素材 {start_path}: {e}")
        else:
            print(f"警告: Start素材不存在 {start_path}")
        
        # 现在绘制所有文字，确保它们位于最上层
        shadow_color1 = (255,255,255)
        shadow_color2 = (0,0,0)
        text_color = (255, 0, 0)  # 红色文字
                
        # 绘制night_circle文字
        for text_info in night_circle_texts:
            text, position, font = text_info['text'], text_info['position'], text_info['font']
            x, y = position
            # 检查坐标是否在图片范围内
            if 0 <= x < background.width and 0 <= y < background.height:
                # 添加文字阴影
                draw.text((x-3, y-3), text, font=font, fill=shadow_color1)
                draw.text((x-1, y-1), text, font=font, fill=shadow_color1)
                draw.text((x+1, y+1), text, font=font, fill=shadow_color2)
                draw.text((x+3, y+3), text, font=font, fill=shadow_color2)
                draw.text((x+5, y+5), text, font=font, fill=shadow_color2)
                draw.text((x+7, y+7), text, font=font, fill=shadow_color2)
                # 添加文字
                draw.text((x, y), text, font=font, fill=(255,155,0))
        
        # 绘制建筑文字
        for text_info in building_texts:
            text, position, font = text_info['text'], text_info['position'], text_info['font']
            x, y = position
            # 检查坐标是否在图片范围内
            if 0 <= x < background.width and 0 <= y < background.height:
                # 添加文字阴影
                draw.text((x+4, y+4), text, font=font, fill=(0,0,0))
                draw.text((x-4, y-4), text, font=font, fill=(0,0,0))
                # 添加文字
                draw.text((x, y), text, font=font, fill=(255,255,0))

        # 绘制神授塔文字
        for text_info in floor_texts:
            text, position, font = text_info['text'], text_info['position'], text_info['font']
            x, y = position
            # 检查坐标是否在图片范围内
            if 0 <= x < background.width and 0 <= y < background.height:
                # 添加文字阴影
                draw.text((x+8, y+8), text, font=font, fill=(0,0,0))
                draw.text((x-8, y-8), text, font=font, fill=(0,0,0))
                # 添加文字
                draw.text((x, y), text, font=font, fill=(255,255,0))
        
        # 添加事件描述文字
        # event_flag = row['EventFlag']
        if event_flag in [7705, 7725]:
            # 特殊处理7705和7725
            event_text = f"特殊事件：{name_dict.get(event_flag, event_flag)} {name_dict.get(event_value, event_value)}"
        else:
            event_text = f"特殊事件：{name_dict.get(event_flag, event_flag)}"
        
        # 在指定位置添加事件描述文字
        event_x, event_y = int(round(1200)), int(round(4300))
        # 使用getbbox获取文本尺寸
        bbox = font_event.getbbox(event_text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 检查坐标是否在图片范围内
        if 0 <= event_x < background.width and 0 <= event_y < background.height:
            # 添加文字阴影
            draw.text((event_x+15, event_y+15), event_text, font=font_event, fill=(115,15,230))
            # 添加文字
            draw.text((event_x, event_y), event_text, font=font_event, fill=(255,255,255))
        else:
            print(f"警告: 事件描述文字坐标 ({event_x}, {event_y}) 超出图片范围")
        
        # 缩放图片
        original_width, original_height = background.size
        new_size = (original_width // tran, original_height // tran)
        resized_background = background.resize(new_size, Image.Resampling.LANCZOS)
        
        # 保存图片
        output_path = os.path.join(output_folder, f"map_{ID}.png")
        resized_background.save(output_path)

        print(f"MAP_{ID}已生成")
        
        # 修正计数输出
        if (idx + 1) % 10 == 0:
            print(f"已生成 {idx + 1} 张图片...")
    
    print("所有图片生成完成!")

if __name__ == "__main__":
    DATA_CSV_FILE = "MAP_PATTERN.csv"
    COORDINATES_CSV_FILE = "坐标.csv"
    CONSTRUCT_CSV_FILE = "CONSTRUCT.csv"
    NAME_CSV_FILE = "NAME.csv"  # 新增名称映射文件
    MATERIALS_FOLDER = "素材"
    OUTPUT_FOLDER = "输出"
    FONT_PATH = "simhei.ttf"  # 可以指定字体路径，如 "arial.ttf"
    
    generate_maps_from_csv(
        csv_file=DATA_CSV_FILE,
        materials_folder=MATERIALS_FOLDER,
        coordinates_file=COORDINATES_CSV_FILE,
        construct_file=CONSTRUCT_CSV_FILE,
        name_file=NAME_CSV_FILE,
        output_folder=OUTPUT_FOLDER,
        font_path=FONT_PATH
    )