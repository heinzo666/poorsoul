import os
from git import Repo
full_local_path = "/content/downloadroop"
username = "heinzo666"
password = "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"
remote = f"https://{username}:{password}@github.com/heinzo666/downloadroop.git"
Repo.clone_from(remote, full_local_path)

os.chdir('../downloadroop')
import shutil
shutil.make_archive('HEINZO', 'zip', '/content/poorsoul/output')

backupname = "/content/downloadroop/HEINZO.zip"
backup = ('/content/downloadroop/{file}_{time}.zip')
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
