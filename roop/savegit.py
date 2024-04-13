tgl = datetime.now().strftime("%y%m%d_%H%M%S%f")
os.chdir('..')
cp /content/HEINZO.rar /content/downloadroop

backupname = "/content/downloadroop/HEINZO.rar"

backup = ('/content/downloadroop/D' + str(tgl) + '.rar')

os.rename(backupname, backup)

os.chdir('/content/downloadroop')

git add -A

git commit -a -m "commit"
git remote rm origin

git remote add origin https://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@github.com/heinzo666/downloadroop.git

git push origin main --quiet

os.chdir('..')

cd poorsoul
