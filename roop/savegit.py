tgl = datetime.now().strftime("%y%m%d_%H%M%S%f")
os.chdir('..')
cp /content/HEINZO.rar /content/downloadroop

backupname = "/content/downloadroop/HEINZO.rar"

backup = ('/content/downloadroop/D' + str(tgl) + '.rar')

os.rename(backupname, backup)

os.chdir('/content/downloadroop')
repo = Repo('/content/downloadroop')
repo.git.add('-A')
repo.git.commit('-m', commit)
repo.git.remote.remove.origin

repo.git.remote.add.origin('https://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@github.com/heinzo666/downloadroop.git')

repo.git.push.origin.main

os.chdir('..')

cd poorsoul
