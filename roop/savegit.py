tgl = datetime.now().strftime("%y%m%d_%H%M%S%f")
os.chdir('..')
git config --global user.email "heinzoeimsy@gmail.com
git config --global user.name "heinzo666"
zip -r /content/Heinzo.rar /content/poorsoul/outputs
cp /content/HEINZO.rar /content/downloadroo
backupname = "/content/downloadroop/HEINZO.rar"
backup = ('/content/downloadroop/D' + str(tgl) + '.rar')
os.rename(backupname, backup)

cd downloadroop

git add -A

git commit -a -m "commit"

git remote rm origin

git remote add origin https://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@github.com/heinzo666/downloadroop.git

git push origin main --quiet

os.chdir('..')

cd poorsoul
