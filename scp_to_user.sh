if [ -z "$1" ]
  then
    echo "No argument supplied"
    exit
fi


FILENAME=$1
scp -i ./user_bullseye.id_rsa -P 10021  -o "StrictHostKeyChecking no" -r $FILENAME MyUser@localhost:/home/MyUser 
