#im gleichen verzeichnis muss die updater.json liegen um
#regelmaesige updates zu ermoeglichen
import os
import git

path = ''
seperator = '/'
update_folder = ''

def main():
    global path
    path = os.getcwd()
    check_folder = False
    for file in os.listdir(path):
        if file == 'IotAdapter':
            check_folder = True
    if not check_folder:
        move_updater()
        return

    need_to_update = check_version()

    if need_to_update == 2:
        pass #no network
    elif need_to_update:
        update()

    #wait 24hours

def move_updater():
    global path
    new_path = '/'.join(path.split(seperator)[:-1])
    order = 'cp ' + path + '/updater.py ' + new_path + '/updater.py'
    os.system(order)
    order = 'cp ' + path + '/updater.json ' + new_path + '/updater.json'
    os.system(order)
    order = 'python ' + new_path + '/updater.py'
    os.system(order)
    #register updater in rc.local oder in cronjob


def check_version():
    path_of_updates = path + '/IotAdapter/updates'
    lastest_version = '0'
    for file in os.listdir(path):
        version = file.replace('update', '')
        if version > lastest_version:
            lastest_version = version

    #send https request an license.enwatmon.de fuer version vergleich
    url = 'https://license.enwatmon.de/version'
    myobj = {'version': int(lastest_version)}
    try:
        x = requests.post(url, data = myobj)
    except Exception as e:
        print(e)

    if not x:
        return 2

    return x.text == 'new version available'
def update():
    #git pull muss config auslassen bzw in gitignore schreiben
    g = git.cmd.Git(path)
    g.stash()
    g.pull()

    lastest_version = '0'

    for file in os.listdir(path):
        version = file.replace('update', '')
        if version > lastest_version:
            lastest_version = version
            global update_folder
            update_folder = file

    if not update_folder:
        print('no updates available')
        return
    f = open(update_folder + '/update.sh')
    orders = f.readlines()

    for order in orders:
        print('\n' + order)
        print(Fore.GREEN + 'Order executing...')
        res = os.popen(order).read()
        print(res)
        print(Fore.GREEN + 'Order done\n')

    print('done')
if __name__ == '__main__':
    main()
