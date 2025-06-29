import os
import cv2
import shutil
import sys
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
    return detected_match, match_percentage


class VideoGame:
    def __init__(self, name):
        self.name = name

    def get_scenario(self, scenario_frame, scenario_location):
        converted_frame = cv2.cvtColor(scenario_frame, cv2.COLOR_BGR2RGB)
        image_frame = Image.fromarray(converted_frame)
        return best_match(self.name, 'scenarios', image_frame, scenario_location)

    def get_starring(self, character_frame, character_location):
        converted_frame = cv2.cvtColor(character_frame, cv2.COLOR_BGR2RGB)
        image_frame = Image.fromarray(converted_frame)
        return best_match(self.name, 'characters', image_frame, character_location)

    def get_punctuation(self, punctuation_frame, punctuation_location):
        (thresh, punctuation_frame) = cv2.threshold(punctuation_frame, 120, 255, cv2.THRESH_BINARY)
        converted_frame = cv2.cvtColor(punctuation_frame, cv2.COLOR_BGR2RGB)
        image_punctuation = Image.fromarray(converted_frame)
        punct_focused = image_punctuation.crop(punctuation_location)
        text = pytesseract.image_to_string(punct_focused, config='--psm 7--oem 2 -c tessedit_char_whitelist=0123456789')
        text = text[:-2]
        return text

    def rename_file(self, old_name, new_name):
        title = new_name.split('.m')[0]
        mp4_file = MP4(videos_folder + old_name)  # load the video file
        mp4_file["\xa9nam"] = title  # change video title
        mp4_file.save()  # save changes

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
            video.set(1, 0)  # set the first frame of video
            ret_init, frm_init = video.read()  # first frame is saved
            video.set(1, length - 1)  # set the last frame of video
            ret_final, frm_final = video.read()  # last frame is saved

            if not ret_final:   # in case final frame is not correctly grabbed
                video.set(1, length - 10)  # set another frame of video
                ret_final, frm_final = video.read()  # last frame is saved

            if 'battlefield™ 1' in file.lower():
                print('Video found for battlefield 1', file)
                game = VideoGame('battlefield 1')
                video.set(1, length - int(fps*22))  # set the last frame of video minus 22 seconds
                ret_punt, frm_punt = video.read()   # last frame is saved
                scenario, _ = game.get_scenario(frm_final, (47, 54, 675, 74))
                try:
                    punctuation = game.get_punctuation(frm_punt, (850, 485, 1060, 545))
                    int(punctuation)
                except ValueError:
                    video.set(1, length - int(fps * 27))  # set the last frame of video minus 27 seconds
                    ret_punt, frm_punt = video.read()  # last frame is saved
                    punctuation = game.get_punctuation(frm_punt, (850, 485, 1060, 545))

                name = 'Battlefield 1 ' + scenario + ' ' + punctuation + '.mp4'
                print('New name: ' + name)

            elif 'resident evil 4' in file.lower():
                print('Video found for resident evil 4', file)
                game = VideoGame('resident evil 4')
                score_image = Image.open(videos_folder + 'Renombrar videos/resident evil 4/total score.png')
                possible_score_locations = {0: 694, 1: 724, 2: 648, 3: 620}  # label score can be in 4 locations
                opt = 0
                for i in range(4):
                    chop_score_label = frm_final[possible_score_locations[i]:possible_score_locations[i] + 36, 652:839]
                    chop_score_label = cv2.cvtColor(chop_score_label, cv2.COLOR_BGR2RGB)
                    chop_score_label = Image.fromarray(chop_score_label)
                    if similarity(score_image, chop_score_label) > 90:
                        opt = i

                vert_pos = {0: 683, 1: 714, 2: 636, 3: 605}     # score can be in one of these locations
                scenario, _ = game.get_scenario(frm_init, (1100, 0, 1920, 1080))
                character, _ = game.get_starring(frm_final, (0, 0, 600, 540))
                punctuation = game.get_punctuation(frm_final, (1023, vert_pos[opt], 1270, vert_pos[opt] + 62))
                name = 'Resident Evil 4 Remake Mercenaries ' + scenario + ' ' + character + ' ' + punctuation + '.mp4'
                print('New name: ' + name)

            elif 'resident evil 5' in file.lower():
                print('Video found for resident evil 5', file)
                game = VideoGame('resident evil 5')
                scenario, _ = game.get_scenario(frm_final, (580, 80, 1380, 180))
                punctuation = game.get_punctuation(frm_final, (1275, 657, 1540, 706))
                r_character, r_certainty = game.get_starring(frm_init, (1485, 812, 1630, 954))  # analyzing right side
                l_character, l_certainty = game.get_starring(frm_init, (280, 818, 431, 956))  # analyzing left side
                if r_certainty > l_certainty:
                    character = r_character
                else:
                    character = l_character

                name = 'Resident Evil 5 Mercenaries ' + scenario + ' ' + character + ' ' + punctuation + '.mp4'
                print('New name: ' + name)

            elif 'resident evil 6' in file.lower():
                print('Video found for resident evil 6', file)
                game = VideoGame('resident evil 6')
                scenario, _ = game.get_scenario(frm_final, (457, 82, 761, 124))
                character, _ = game.get_starring(frm_final, (146, 156, 500, 206))
                punctuation = game.get_punctuation(frm_final, (551, 820, 776, 880))
                name = 'Resident Evil 6 Mercenaries ' + scenario + ' ' + character + ' ' + punctuation + '.mp4'
                print('New name: ' + name)

            elif 'resident evil village' in file.lower():
                print('Video found for resident evil village', file)
                game = VideoGame('resident evil village')
                scenario, _ = game.get_scenario(frm_init, (114, 71, 747, 183))
                character, _ = game.get_starring(frm_init, (684, 846, 1266, 915))
                punctuation = game.get_punctuation(frm_final, (762, 337, 1190, 411))
                name = 'Resident Evil Village Mercenaries ' + scenario + ' ' + character + ' ' + punctuation + '.mp4'
                print('New name: ' + name)
            else:
                print('There is no video files to be processed')

            video.release()
            game.rename_file(file, name)  # this is used to rename the video file
