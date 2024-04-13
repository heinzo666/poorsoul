import os
os.chdir('../downloadroop')
import shutil
shutil.make_archive(HEINZO, 'zip', '/content/downloadroop')
shutil.copyfile('/content/HEINZO.zip', '/content/downloadroop/Heinzo.zip')

backupname = "/content/downloadroop/HEINZO.zip"

backup = ('/content/downloadroop/D.zip')

os.rename(backupname, backup)


repo = Repo('/content/downloadroop')
repo.git.add('-A')
repo.git.commit('-m', commit)
repo.git.remote.remove.origin

repo.git.remote.add.origin('https://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@github.com/heinzo666/downloadroop.git')

repo.git.push.origin.main

os.chdir('../poorsoul')
