# HOW TO PARROTFISH

## Set your remote Aquarium server

## Pull code into a folder

## Version control with Git
For example, say we have two Parrotfish directories, /nursery and /production, which are associated with your Aquarium nursery and production servers respectively. Here is a suggested method for writing code safely:
1. Pull most recent code into /nursery
2. Make a git branch my_update, and commit awesome code
3. Navigate to /production, and pull most recent code from remote
4. In /production, add /nursery as a remote git repository with (ONLY NEED TO DO THIS STEP ONCE)
```git
git remote add nursery ../nursery
```
and then make sure you can see the most recent nursery branches with
```git
git remote update
```
5. Make a new branch for /production, and patch in desired files from your nursery branch with
```git
git checkout --patch nursery/my_update "Cloning/Rehydrate Primer.rb" "Cloning/Order Primer.rb"
```

## Push code to production