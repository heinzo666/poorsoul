import os
os.chdir('../downloadroop')
import shutil
shutil.make_archive('HEINZO', 'zip', '/content/poorsoul/output')

from git import Repo
backupname = "/content/downloadroop/HEINZO.zip"

backup = ('/content/downloadroop/{file}_{time}.zip')

os.rename(backupname, backup)


repo = Repo('/content/downloadroop')
repo.git.add('-A')
repo.git.commit('-a', '-m', 'commit')
remote = repo.remote(name='origin')
remote.push(refspec=(':delete_me'))

#repo.git.remote.remove.origin

repo.git.remote.add.origin('https://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@github.com/heinzo666/downloadroop.git')

repo.git.push.origin.main

os.chdir('../poorsoul')
