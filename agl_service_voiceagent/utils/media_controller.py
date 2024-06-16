# SPDX-License-Identifier: Apache-2.0
#
# Copyright (c) 2023 Malik Talha
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from mpd import MPDClient
import json
from agl_service_voiceagent.utils.config import get_config_value, get_logger
from agl_service_voiceagent.utils.common import load_json_file, words_to_number


class MediaController:
    def __init__(self):
        self.client = MPDClient()
        self.ip = get_config_value('MPD_IP')
        self.port = get_config_value('MPD_PORT')
        self.is_connected = self.connect()

    def connect(self):
        try:
            self.client.connect(self.ip, self.port)
            return True
        except Exception as e:
            print(f"[-] Error: Failed to connect to MPD server: {e}")
            return False

    def play(self, uri):
        '''
        Play the media file at the specified URI.

        Args:
            uri (str): The URI of the media file to play.

        '''
        if not self.is_connected:
            print("[-] Error: MPD client is not connected.")
            return False

        try:
            self.client.clear()
            self.client.add(uri)
            self.client.play()
            return True
        except Exception as e:
            print(f"[-] Error: Failed to play media: {e}")
            return False

    def stop(self):
        '''
        Stop the media player.
        '''
        if not self.is_connected:
            print("[-] Error: MPD client is not connected.")
            return False
        try:
            self.client.stop()
            return True
        except Exception as e:
            print(f"[-] Error: Failed to stop media: {e}")
            return False

    def pause(self):
        '''
        Pause the media player.
        '''
        if not self.is_connected:
            print("[-] Error: MPD client is not connected.")
            return False
        try:
            self.client.pause()
            return True
        except Exception as e:
            print(f"[-] Error: Failed to pause media: {e}")
            return False

    def resume(self):
        '''
        Resume the media player.
        '''
        if not self.is_connected:
            print("[-] Error: MPD client is not connected.")
            return False
        try:
            self.client.play()
            return True
        except Exception as e:
            print(f"[-] Error: Failed to resume media: {e}")
            return False
        
    def next(self):
        '''
        Play the next track in the playlist.
        '''
        if not self.is_connected:
            print("[-] Error: MPD client is not connected.")
            return False
        try:
            self.client.next()
            return True
        except Exception as e:
            print(f"[-] Error: Failed to play next track: {e}")
            return False

    def previous(self):
        '''
        Play the previous track in the playlist.
        '''
        if not self.is_connected:
            print("[-] Error: MPD client is not connected.")
            return False
        try:
            self.client.previous()
            return True
        except Exception as e:
            print(f"[-] Error: Failed to play previous track: {e}")
            return False

    def close(self):
        self.client.close()
        self.client.disconnect()

