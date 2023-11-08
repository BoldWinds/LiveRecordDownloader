import json


class LiveRoomConfig:
    # 一个直播间的设置
    def __init__(self, url: str, description: str, start_time: str, is_recording: bool, is_living: str):
        self.url = url
        self.description = description
        self.start_time = start_time
        self.is_recording = is_recording
        self.is_living = is_living

    def to_dict(self):
        return {
            'url': self.url,
            'description': self.description,
            'start_time': self.start_time,
            'is_recording': self.is_recording,
            'is_living': self.is_living
        }

    def __repr__(self):
        return json.dumps({
            'url': self.url,
            'description': self.description,
            'start_time': self.start_time,
            'is_recording': self.is_recording,
            'is_living': self.is_living
        }, indent=4)


class Config:
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            config_str = f.read()
            config = json.loads(config_str)
        self.config_path = config_path
        self.username = config['username']
        self.password = config['password']
        self.video_save_path = config['video_save_path']
        self.video_quality = config['video_quality']
        self.dy_cookie = config['dy_cookie']
        self.live_rooms = [LiveRoomConfig(**url) for url in config['live_rooms']]

    # 查找url_to_find对应的UrlConfig对象，然后更新其中的内容
    def update_live_room(self, url_to_find: str, updates: dict):
        for room in self.live_rooms:
            if room.url == url_to_find:
                # Update the attributes of the UrlConfig with new data
                if 'url' in updates:
                    room.url = updates['url']
                if 'description' in updates:
                    room.description = updates['description']
                if 'start_time' in updates:
                    room.start_time = updates['start_time']
                if 'is_recording' in updates:
                    room.is_recording = updates['is_recording']
                if 'is_living' in updates:
                    room.is_living = updates['is_living']
                print(f"Room updated: {room.url}")
                return
        print(f"Room not found: {url_to_find}")

    # Method to synchronize object data back to the file
    def save_config(self):
        config = {
            'username': self.username,
            'password': self.password,
            'video_save_path': self.video_save_path,
            'video_quality': self.video_quality,
            'dy_cookie': self.dy_cookie,
            'live_rooms': [room.to_dict() for room in self.live_rooms]  # Assuming UrlConfig has a to_dict() method
        }
        with open(self.config_path, 'w', encoding='utf-8') as file:
            json.dump(config, file, ensure_ascii=False, indent=4)

    # Method to output the class data in JSON format
    def __repr__(self):
        config = {
            'username': self.username,
            'password': self.password,
            'video_save_path': self.video_save_path,
            'video_quality': self.video_quality,
            'dy_cookie': self.dy_cookie,
            'live_rooms': [room.to_dict() for room in self.live_rooms]
        }
        return json.dumps(config, ensure_ascii=False, indent=4)

