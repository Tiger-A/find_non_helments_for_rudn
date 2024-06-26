import cv2
from ultralytics import YOLO
import os
import shutil
import numpy as np
import glob
import time
import telebot # Установить pyTelegramBotAPI


TOKEN = '6862727787:AAFYwAn9C5F8okTHA0GnWmqfmyvdHRN5tKk' # Создать telegram-bot и получить TOKEN
# Создать  группу в telegram, назначить telegram-bot админом группы
# Получить chat_id группы и вставить ниже
chat_id = '612376177'
bot = telebot.TeleBot(TOKEN)

# =======================================



# Папки архива и общая папка со всеми изображениями
fin = '...dir/archive' # архив с нарушителями
fin1 = '...dir/all_frame' # Все изображения, если нужно

if not os.path.exists(fin):
    os.makedirs(fin)

if not os.path.exists(fin):
    os.makedirs(fin1)

# Папки архива и общую папку достаточно создать один раз
if os.path.exists(fin):
    shutil.rmtree(fin)
if os.path.exists(fin1):
    shutil.rmtree(fin1)

os.mkdir(fin)
os.mkdir(fin1)
# =======================================

model_path = 'C:\\Users\\Admin\\Downloads\\best-3_classes-m.pt'

# Загрузите модель YOLOv8
model = YOLO(model_path)

# Путь к видеофайлу или url-камеры 
#video_path = 'C:\Users\Admin\Downloads\trim-video-online.com_1705759881_ЦОД12202309061633347_WMskO0lK.avi'
video_path = 'C:\\Users\\Admin\\Downloads\\trim-video-online.com_1705759881_ЦОД12202309061633347_WMskO0lK.avi'

cap = cv2.VideoCapture(video_path)
num_cap = cap.get(7)
num = 1
lst_id = set()

# Цикл по кадрам видео
while cap.isOpened():
    # Чтение кадра из видео
    ret, frame = cap.read()
    # Путь к файлу в архиве. Имя файла - время его записи.
    file_name = time.strftime("%Y.%m.%d_%H.%M.%S") + ".jpg"
    name_save = os.path.join(fin, file_name)
    # Путь к файлу в общей папке. Необязательно.
    name_save1 = os.path.join(fin, f"{num:05}.jpg")

    if ret:
        # Технический параметр. Необязательно
        print(f"Кадр {num} из {num_cap}")

        # Обнаруживаем бескасочников
        # Трек включен для фиксации только новых бескасочников
        results = model.track(frame,
                              classes=[1, 2],
                              verbose=False,
                              conf=0.5,
                              persist=True,
                              stream=True,
                              tracker='botsort.yaml' # в доках ultralytics скачать
        )

        for box in results:
            lst_res = box.boxes.data.cpu().numpy().astype(int).tolist()

            lst_2 = []  
            for n, i in enumerate(lst_res):
                if len(i) == 7 and lst_res[n][6] != 1:
                    lst_2.append([lst_res[n][0], lst_res[n][1], lst_res[n][2], lst_res[n][3]])
                if len(i) == 7 and lst_res[n][6] == 1:
                    x1, y1, x11, y11 = (lst_res[n][0], lst_res[n][1], lst_res[n][2], lst_res[n][3])
                    # Необязательный параметр. bb головы без каски
                    cv2.rectangle(frame, (x1, y1), (x11, y11), (255, 0, 255), 3)
                    
                    for m in lst_2:
                        if abs(m[2] - x11) < 50: # Ловим близость ББ человека и ББ головы без каски
                            # Необязательный параметр. bb человека без каски
                            cv2.rectangle(frame, (m[0], m[1]), (m[2], m[3]), (0, 255, 255), 3)
                        
                            # Сохраняем изображение с только новым бескасочником
                            # и отправлям изображение в группу в телеграмм
                            if i[-3] not in lst_id:
                                lst_id.add(i[-3])
                                resized = cv2.resize(frame, (480, 360))
                                cv2.imwrite(name_save, resized)
                                # Необязательный параметр
                                print("file_name", file_name)
                                # Учитываем, что в телеграмм подряд нельзя много изображений отправить
                                # Возможно установить параметр, чтобы не чаще раз/минута, например
                                if os.stat(name_save).st_size != 0:
                                    with open(name_save, 'rb') as f:
                                        bot.send_photo(chat_id, f)
                                        time.sleep(10) # Страховка для Телеграмм,
                                                       # чтобы не было много загрузок за короткое время

                      
        # Сохранение изображений в общую папку. Необязательно
        frame = cv2.resize(frame, (640, 480))
        # cv2.imwrite(name_save1, frame)
        # Вывод на монитор. Необязательно
        cv2.imshow("Отслеживание", frame)
        num += 1

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    else:
        break

cap.release()
cv2.destroyAllWindows()
