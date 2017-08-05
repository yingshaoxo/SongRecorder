#qpy:kivy
# -*- coding: UTF-8 -*-

try:
    import sys 
    reload(sys) 
    sys.setdefaultencoding("utf-8")
except:
    pass
	
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen

from kivy.uix.popup import Popup
from kivy.core.clipboard import Clipboard
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

import os
import json

from jnius import autoclass, cast
from android import activity


# init all
Environment = autoclass('android.os.Environment')
storage_dir = Environment.getExternalStorageDirectory().getAbsolutePath() 


# For file choice and showing
def select_file(start_dir='/Download'):
    app = App.get_running_app()
    app.target_path = ''

    PythonActivity = autoclass('org.renpy.android.PythonActivity')
    Uri = autoclass('android.net.Uri')
    selectedUri = Uri.parse(storage_dir + start_dir)
    currentActivity = cast('android.app.Activity', PythonActivity.mActivity)

    def on_activity_result(requestCode, resultCode, data):
        print(requestCode)
        print(resultCode)
        #print(data)
        if requestCode == 1:
            if resultCode == -1:
               print('Got target_path!')
               one_uri = data.getData()
               app.target_path = one_uri.getPath()
               
               if app.target_path[:10] != '/external/':
                   print(app.target_path)
                   App.get_running_app().save_setting({'mp3_path': app.target_path})
                   return
               else:
                   filePathColumn = ["_data"]
                   cursor = currentActivity.getContentResolver().query(one_uri, filePathColumn, None, None, None)
                   cursor.moveToFirst()
                   columnIndex = cursor.getColumnIndex(filePathColumn[0])
                   app.target_path = cursor.getString(columnIndex)
                   cursor.close()
                   print(app.target_path)
                   App.get_running_app().save_setting({'mp3_path': app.target_path})
                   return
        print('Fail to get target_path')
        return

    activity.bind(on_activity_result=on_activity_result)
    Intent = autoclass('android.content.Intent')
    intent = Intent(Intent.ACTION_GET_CONTENT)
    intent.addCategory(Intent.CATEGORY_OPENABLE)
    intent.setDataAndType(selectedUri, "resource/folder") 
    currentActivity.startActivityForResult(intent, 1)


# For file sharing
def share_file(path):
    PythonActivity = autoclass('org.renpy.android.PythonActivity')
    Intent = autoclass('android.content.Intent')
    String = autoclass('java.lang.String')
    Uri = autoclass('android.net.Uri')
    File = autoclass('java.io.File')

    shareIntent = Intent(Intent.ACTION_SEND)
    shareIntent.setType('"*/*"')
    imageFile = File(path)
    uri = Uri.fromFile(imageFile)
    parcelable = cast('android.os.Parcelable', uri)
    shareIntent.putExtra(Intent.EXTRA_STREAM, parcelable)

    currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
    currentActivity.startActivity(shareIntent)


# For audio play and record
MediaPlayer = autoclass('android.media.MediaPlayer')
MediaRecorder = autoclass('android.media.MediaRecorder')
AudioSource = autoclass('android.media.MediaRecorder$AudioSource')
OutputFormat = autoclass('android.media.MediaRecorder$OutputFormat')
AudioEncoder = autoclass('android.media.MediaRecorder$AudioEncoder')

recorder = MediaRecorder()
player = MediaPlayer()

aac_path = (storage_dir + '/kivy_recording.aac')

def reset_player():
    if (player.isPlaying()):
        player.stop()
    player.reset()

def restart_player(file_path):
    reset_player()
    try:
        player.setDataSource(file_path)
        player.prepare()
        player.start()
    except:
        player.reset()

def init_recorder():
    recorder.setAudioSource(AudioSource.MIC)
    recorder.setOutputFormat(OutputFormat.MPEG_4)
    recorder.setAudioEncoder(AudioEncoder.AAC)
    recorder.setAudioEncodingBitRate(16 * 44100)
    recorder.setAudioSamplingRate(44100)
    recorder.setOutputFile(aac_path)
    recorder.prepare()


Builder.load_string('''
#:import C kivy.utils.get_color_from_hex

<Widget>:
    font_name:'data/droid.ttf'

<Button>:
    background_normal: 'data/button_normal.png'
    background_down: 'data/button_down.png'
    font_size: 24
    halign: 'center'
    markup: True
    
<LRCLabel@Label>:
    color: C('#101010')
    font_size: 36
    text_size: (self.width, None)
    halign: 'center'
    valign: 'middle'
    padding: (0, 0)
    size_hint: (1, None)
    height: self.texture_size[1]
    markup: True

<ScreenManager>:
    canvas.before: 
        Color: 
            rgba: 1, 1, 1, 1 
        Rectangle: 
            pos: self.pos 
            size: self.size
            
    SettingScreen
    RecordingScreen

<SettingScreen>:
    name: 'setting'
    
    BoxLayout:
        orientation: "vertical"
        padding: 15
        spacing: 15
        
        BoxLayout:
            orientation: "vertical"
            spacing: 15

            Button:
                background_color: C('#FFB510')
                text: '[size=40]Select MP3[/size]'
                on_release: root.select_mp3_button()
            
            Button:
                background_color: C('#BC92F4')
                text: '[size=40]Write LRC[/size]'
                on_release: root.write_lrc_button()
                
        Button:
            background_color: C('#1abc9c')
            text: '[size=60]Start[/size]'
            on_release: root.start_button()

<RecordingScreen>:
    name: 'recording'
    
    BoxLayout:
        orientation: "vertical"
        padding: 15
        spacing: 15
        
        BoxLayout:
            orientation: "vertical"
            spacing: 15
            size_hint: (1, 0.5)
            
            Button:
                id: record_button
                background_color: C('#e74c3c')
                text: '[size=60]Record[/size]'
                on_release: root.manager.record_button()
            Button:
                id: playback_button
                background_color: C('#3498db')
                text: '[size=60]Playback[/size]'
                on_release: root.manager.playback_button()

        ScrollView:
            size_hint: (1, 0.5)
            LRCLabel:
                id: lrc_show
''')


class SettingScreen(Screen):

    def select_mp3_button(self):
        app = self.manager.app
        setting = app.read_setting()

        mp3_path = setting.get('mp3_path')
        if mp3_path != None:
            start_dir = os.path.dirname(mp3_path).replace(storage_dir, '')
            select_file(start_dir)
        else:
            select_file()

    def popup_callback(self, popup_instance):
        # print(popup_instance.content.children)
        lrc = popup_instance.content.children[1].text
        lrc = lrc.strip('\n ')
        self.manager.app.save_setting({u'lrc': lrc})

    def write_lrc_button(self):       
        app = self.manager.app
        setting = app.read_setting()

        lrc  = setting.get('lrc')

        layout = BoxLayout(orientation='vertical', spacing=10)
        popup = Popup(title="What's your LRC?", title_align='center', content=layout, size_hint=(0.8, 0.8), backgroud_color=[0, 0, 0, 0.5])

        def get_purposed_text():
            clipboard_text = Clipboard.paste()
            if lrc == None:
                return clipboard_text
            elif lrc == '':
                return clipboard_text
            else:
                return lrc

        layout.add_widget(TextInput(text=get_purposed_text(), font_size=self.width*0.05, size_hint=(1, 0.9)), index=1)

        saving_button = Button(text='Save', color=[0, 0, 0, 1], size_hint=(1, 0.1))
        saving_button.bind(on_release=popup.dismiss)
        layout.add_widget(saving_button, index=0)

        popup.bind(on_dismiss=self.popup_callback) 
        popup.open()
    
    def start_button(self):
        app = self.manager.app
        setting = app.read_setting()

        mp3_path = setting.get('mp3_path')
        if mp3_path == None: # or mp3_path[-4:0] != '.mp3':
            self.select_mp3_button()
            return
        else:
            self.manager.mp3_path = mp3_path

        lrc = app.read_setting().get('lrc')
        if lrc == None:
            self.write_lrc_button()
            return
        else:
            lrc = lrc.strip('\n ')
            self.manager.get_screen('recording').ids.lrc_show.text = '\n\n' + lrc + '\n\n'
    
        self.manager.current = 'recording'


class RecordingScreen(Screen):
    pass


class ScreenManager(ScreenManager):
    
    def __init__(self, **kwargs):    
        self.app = App.get_running_app()
        self.is_recording = False
        self.is_playbacking = False
        super(ScreenManager, self).__init__(**kwargs)
    
    def begin_recording(self):
        init_recorder()
        restart_player(self.mp3_path)
        recorder.start()
        self.is_recording = True
        self.get_screen('recording').ids.record_button.text = '[size=60]Tap to end[/size]'

    def end_recording(self):
        reset_player()
        recorder.stop()
        recorder.reset()
        self.is_recording = False
        self.get_screen('recording').ids.record_button.text = '[size=60]Record[/size]'

    def begin_playing(self):
        restart_player(aac_path)
        self.is_playbacking = True
        self.get_screen('recording').ids.playback_button.text = '[size=60]Tap to stop[/size]'

    def stop_playing(self):
        reset_player()
        self.is_playbacking = False
        self.get_screen('recording').ids.playback_button.text = '[size=60]Playback[/size]'
        
    def record_button(self):
        if self.is_playbacking:
            self.stop_playing()

        if self.is_recording:
            self.end_recording()
        else:
            self.begin_recording()

    def playback_button(self):
        if self.is_recording:
            self.end_recording()

        if self.is_playbacking:
            self.stop_playing()
        else:
            self.begin_playing()


class SongRecorderApp(App):

    def __init__(self, **kwargs):
        self.app_path =os.path.dirname(os.path.abspath('.'))
        self.setting_path = os.path.join(self.app_path, 'setting.json')
        if os.path.exists(self.setting_path) == False:
            self.write_setting(json.dumps({'first_launch': False}))
        super(SongRecorderApp, self).__init__(**kwargs)
    
    def read_setting(self):
        with open(self.setting_path, 'r') as f:
            text = f.read()
        text = text.strip(' \n')
        return json.loads(text)
    
    def save_setting(self, new_dict):
        old_dict = self.read_setting()
        old_dict.update(new_dict)
        text = json.dumps(old_dict)
        with open(self.setting_path, 'w') as f:
            f.write(text)

    def write_setting(self, text):
        with open(self.setting_path, 'w') as f:
            f.write(text)

    def build(self):
        self.bind(on_start=self.post_build_init)
        return ScreenManager()
   
    def post_build_init(self, ev):
        from kivy.base import EventLoop
        EventLoop.window.bind(on_keyboard=self.hook_keyboard) 
    
    def hook_keyboard(self, window, key, *largs):
        print(key)
        if key == 27: # -- back key
            if(self.root.current=='setting'): 
                exit()
                #App.get_running_app().stop()
            self.root.current='setting' 

            return True
        if key == 319 or key == 1073741942: # -- munu key
            share_file(aac_path)
            return True


SongRecorderApp().run()
