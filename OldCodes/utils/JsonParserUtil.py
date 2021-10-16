from collections import OrderedDict
from json import loads


def loadRowJsonAsDictFromFile(file_path):
    with open(file_path, 'r') as fh:
        data = fh.read()
    try:
        rawJsonObjects = loads(data,object_pairs_hook=OrderedDict)
        #print("Raw json objects are"+str(json.dumps(rawJsonObjects)))
        return  rawJsonObjects
    except Exception as ex:  # pylint: disable=broad-except
        print('Could not parse JSON from file (ex): {0}'.format(str(ex)))
        print("Exiting!!")
        exit(1)