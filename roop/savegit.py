import os
from git import Repo
import datetime as dt
tgl = dt.datetime.now().strftime("%y%m%d_%H%M%S%f")
os.chdir('../downloadroop')
import shutil
shutil.make_archive('HEINZO', 'zip', '/content/poorsoul/output')
full_local_path = "/content/downloadroop"

backupname = "/content/downloadroop/HEINZO.zip"
backup = ('/content/downloadroop/DF' + str(tgl) + '.zip')
os.rename(backupname, backup)


repo = Repo(full_local_path)
repo.git.add("-A")
repo.index.commit("user_deepfakes")

#repo = Repo(full_local_path)
origin = repo.remote(name="origin")
origin.push()

#repo = Repo('/content')
#repo.git.add('-A')
#repo.git.commit('-a', '-m', 'commit')
#remote = repo.remote(name='origin')
#remote.push(refspec=(':delete_me'))

#repo.git.remote.remove.origin

#repo.git.remote.add.origin('https://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@github.com/heinzo666/downloadroop.git')

#repo.git.push.origin.main

os.chdir('../poorsoul')
