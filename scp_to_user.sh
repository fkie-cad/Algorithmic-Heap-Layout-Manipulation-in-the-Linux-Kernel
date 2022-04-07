if [ -z "$1" ]
  then
    echo "No argument supplied"
    exit
fi


FILENAME=$1
scp  -P 10021  -o "StrictHostKeyChecking no" -r $FILENAME he1n@localhost:/home/he1n 
