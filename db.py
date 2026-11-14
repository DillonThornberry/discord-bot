from pymongo import MongoClient
from os import getenv
from dotenv import load_dotenv

load_dotenv()

mongo_client = MongoClient(getenv('MONGO_URI'))

db = mongo_client['discord_bot']

collection = db['main']

def get_leaderboard(category):
    document = collection.find_one(
        {"Category": category}
    )

    if document is None:
        return []

    return document['Leaderboard']



def submit_time(category, user_id, user_name, time_seconds, time_str):
    user_id = str(user_id)

    result = collection.update_one(
        {
            "Category": category,
            "Leaderboard.UserId": user_id
        },
        {
            "$set": {
                "Leaderboard.$.Time": time_seconds,
                'Leaderboard.$.DisplayTime': time_str
            }
        }
    )

    if result.matched_count == 0:
        collection.update_one(
            {"Category": category},
            {
                "$push": {
                    "Leaderboard": {
                        "UserId": user_id,
                        "DisplayName": user_name,
                        "Time": time_seconds,
                        "DisplayTime": time_str
                    }
                }
            }
        )
        print('time added')
    else:
        print('time updated')


USER_IDS = {
    '477950249596354582': 'Nation',
    '1324735698300833793': 'Walker',
    '330421550534885386': 'Ape',
    '706712798696308817': 'Toni',
    '664950169132859453': 'Tank',
    '258713391093252106': 'Yard'
}

def sec_to_time(secs):
    hours = secs // 3600
    secs -= hours * 3600
    
    mins = secs // 60
    secs -= mins * 60


    return f'{str(hours) + ':' if hours > 0 else ''}{mins if mins >= 10 else '0' + str(mins)}:{secs if secs >= 10 else '0' + str(secs)}'


def time_to_sec(time_str):
    parts = list(map(int, time_str.split(":")))
    seconds = 0

    for part in parts:
        seconds = seconds * 60 + part

    return seconds



initial_times = {
    '16 Star': [
        {
            'UserId': '477950249596354582',
            'DisplayName': 'Nation',
            'Time': time_to_sec('16:48'),
            'DisplayTime': sec_to_time(time_to_sec('16:48'))
        },
        {
            'UserId': '1324735698300833793',
            'DisplayName': 'Walker',
            'Time': time_to_sec('20:01'),
            'DisplayTime': sec_to_time(time_to_sec('20:01'))
        },
        {
            'UserId': '330421550534885386',
            'DisplayName': 'Ape',
            'Time': time_to_sec('17:01'),
            'DisplayTime': sec_to_time(time_to_sec('17:01'))
        },
        {
            'UserId': '706712798696308817',
            'DisplayName': 'Toni',
            'Time': time_to_sec('16:55'),
            'DisplayTime': sec_to_time(time_to_sec('16:55'))
        },
        {
            'UserId': '664950169132859453',
            'DisplayName': 'Tank',
            'Time': time_to_sec('17:51'),
            'DisplayTime': sec_to_time(time_to_sec('17:51'))
        },
        {
            'UserId': '258713391093252106',
            'DisplayName': 'Yard',
            'Time': time_to_sec('18:12'),
            'DisplayTime': sec_to_time(time_to_sec('18:12'))
        },
    ],
    '70 Star': [
        {
            'UserId': '477950249596354582',
            'DisplayName': 'Nation',
            'Time': time_to_sec('1:12:41'),
            'DisplayTime': sec_to_time(time_to_sec('1:12:41'))
        },
        {
            'UserId': '330421550534885386',
            'DisplayName': 'Ape',
            'Time': time_to_sec('58:30'),
            'DisplayTime': sec_to_time(time_to_sec('58:30'))
        },
        {
            'UserId': '706712798696308817',
            'DisplayName': 'Toni',
            'Time': time_to_sec('53:46'),
            'DisplayTime': sec_to_time(time_to_sec('53:46'))
        },
        {
            'UserId': '664950169132859453',
            'DisplayName': 'Tank',
            'Time': time_to_sec('1:01:03'),
            'DisplayTime': sec_to_time(time_to_sec('1:01:03'))
        },
        {
            'UserId': '258713391093252106',
            'DisplayName': 'Yard',
            'Time': time_to_sec('1:08:29'),
            'DisplayTime': sec_to_time(time_to_sec('1:08:29'))
        },
    ],
    '1 Star': [
        {
            'UserId': '477950249596354582',
            'DisplayName': 'Nation',
            'Time': time_to_sec('8:19'),
            'DisplayTime': sec_to_time(time_to_sec('8:19'))
        },
        {
            'UserId': '330421550534885386',
            'DisplayName': 'Ape',
            'Time': time_to_sec('8:42'),
            'DisplayTime': sec_to_time(time_to_sec('8:42'))
        },
        {
            'UserId': '664950169132859453',
            'DisplayName': 'Tank',
            'Time': time_to_sec('10:37'),
            'DisplayTime': sec_to_time(time_to_sec('10:37'))
        },
        {
            'UserId': '258713391093252106',
            'DisplayName': 'Yard',
            'Time': time_to_sec('9:38'),
            'DisplayTime': sec_to_time(time_to_sec('9:38'))
        },
    ]
}

def main():
    for lb in initial_times:
        for t in initial_times[lb]:
            submit_time(lb, t['UserId'], t['DisplayName'], t['Time'], t['DisplayTime'])


if __name__ == '__main__':
    None


