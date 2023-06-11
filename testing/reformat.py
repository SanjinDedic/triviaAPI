import json, random

#load master.json file
def indent():
    with open('mega.json') as f:
        data = json.load(f)
        #save with indent
        with open('mega.json', 'w') as f:
            json.dump(data, f, indent=4)
        

def block_answers():
    with open('mega.json') as f:
        data = json.load(f)
        #replace all the answers with "UNKNOWN"
        for i in data:
            i['answer'] = 'UNKNOWN'
        #save with indent
        with open('super_a.json', 'w') as f:
            json.dump(data, f, indent=4)


def randomise_points():
    with open('super.json') as f:
        data = json.load(f)
        #replace all the answers with "UNKNOWN"
        for i in data:
            i['points'] = random.choice([10,20,30,40,50])
        #save with indent
        with open('super_a.json', 'w') as f:
            json.dump(data, f, indent=4)


block_answers()