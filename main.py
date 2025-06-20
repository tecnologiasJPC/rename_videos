import os
import cv2
import shutil
import numpy as np
from PIL import Image
from PIL import ImageChops
from mutagen.mp4 import MP4
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

videos_folder = 'C:/Users/john_/Videos/Captures/'


def similarity(im1, im2):
    dif = ImageChops.difference(im1, im2)
    return 100 - np.mean(np.array(dif))


def best_match(game_name, category, image_frame, section):
    location = videos_folder + 'Renombrar videos/' + game_name + '/' + category
    options = os.listdir(location)
    options_quantity = len(options)
    match_percentage = 0  # it goes from 0 to 100
    detected_match = ''     # here is the string for the scenario
    for image in range(0, options_quantity, 1):
        reference_image = Image.open(location + '/' + options[image])
        current_image = image_frame.crop(section)
        percentage = similarity(reference_image, current_image)
        if percentage > match_percentage:
            match_percentage = percentage
            detected_match = options[image].replace('.png', '')
    return detected_match


class VideoGame:
    def __init__(self, name):
        self.name = name

    def get_scenario(self, scenario_frame, scenario_location):
        converted_frame = cv2.cvtColor(scenario_frame, cv2.COLOR_BGR2RGB)
        image_frame = Image.fromarray(converted_frame)
        return best_match(self.name, 'scenarios', image_frame, scenario_location)

    def get_starring(self):
        pass

    def get_punctuation(self, punctuation_frame, punctuation_location):
        converted_frame = cv2.cvtColor(punctuation_frame, cv2.COLOR_BGR2RGB)
        image_punctuation = Image.fromarray(converted_frame)
        punct_focused = image_punctuation.crop(punctuation_location)
        text = pytesseract.image_to_string(punct_focused, config='--psm 7--oem 2 -c tessedit_char_whitelist=0123456789')
        text = text[:-2]
        return text

    def rename_file(self, old_name, new_name):
        title = new_name.split('.m')[0]
        mp4_file = MP4(videos_folder + self.name)  # Cargar el archivo de video
        mp4_file["\xa9nam"] = title  # Cambiar el título
        mp4_file.save()  # Guardar los cambios
        try:
            os.rename(videos_folder + old_name, videos_folder + new_name)
            shutil.move(videos_folder + new_name, videos_folder + self.name)
        except FileNotFoundError:
            print("File did not found")
        except Exception as e:
            print("Fail to rename")


if __name__ == '__main__':
    files = os.listdir(videos_folder)
    for file in files:
        if '.mp4' in file:  # it selects only video files
            video = cv2.VideoCapture(videos_folder + file)  # it reads video to analyze
            length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))   # it gets the length of video in frames
            fps = video.get(cv2.CAP_PROP_FPS)   # it gets the frames per second
            video.set(1, length - 1)  # set the last frame of video
            ret_final, frm_final = video.read()  # last frame is saved

            if 'battlefield™ 1' in file.lower():
                print('Video found for battlefield 1', file)
                video.set(1, length - int(fps*22))  # set the last frame of video minus 22 seconds
                ret_punt, frm_punt = video.read()   # last frame is saved

                juego = VideoGame('Battlefield 1')
                scenario = juego.get_scenario(frm_final, (47, 54, 675, 74))
                #print('Escenario detectado:', scenario)

                try:
                    punctuation = juego.get_punctuation(frm_punt, (850, 485, 1060, 545))
                    int(punctuation)
                except ValueError:
                    #print('No se detecto puntuacion, se vuelve a intentar')
                    video.set(1, length - int(fps * 27))  # set the last frame of video minus 22 seconds
                    ret_punt, frm_punt = video.read()  # last frame is saved
                    punctuation = juego.get_punctuation(frm_punt, (850, 485, 1060, 545))

                #print('Puntuacion detectada:', punctuation)
                name = 'Battlefield 1 ' + scenario + ' ' + punctuation + '.mp4'
                print('New name: ' + name)

            #juego.rename_file(file, name)  #this is used to rename the video file
            video.release()
