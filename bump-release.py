import os
import sys

os.system('git checkout main')
os.system('git pull')

from cid._version import __version__ as old_ver

bump='patch'
if len(sys.argv)>1:
	bump = sys.argv[1]

maj, minor, patch = map(int, old_ver.split('.'))

if bump=='patch':
	new_ver = '.'.join(map(str,[maj, minor, patch + 1]))
elif bump=='minor':
	new_ver = '.'.join(map(str,[maj, minor + 1, 0]))
else:
	raise NotImplementedError('only patch and minor are implemented')

os.system(f"git checkout -b 'release/{new_ver}'")


tx = open('cid/_version.py').read()
with open('cid/_version.py', "w") as f:
	f.write(tx.replace(f"version__ = '{old_ver}'", f"version__ = '{new_ver}'"))

tx = open('cfn-templates/cid-cfn.yml').read()
with open('cfn-templates/cid-cfn.yml', "w") as f:
	f.write(tx.replace(f"{old_ver}", f"{new_ver}"))


os.system('git diff HEAD --unified=0')
print('to undo:\n git checkout HEAD -- cfn-templates/cid-cfn.yml cid/_version.py')
print(f"to continue:\n git commit -am 'release {new_ver}'; git push origin 'release/{new_ver}'")
