mongoexport -v -u nirg -p dilk2d123 -h troup.mongohq.com:10001 -d ngc-registration -c Operations --type=json --out ~/Documents/teman_utf8_back.csv

mongoimport -v -u nirg -p dilk2d123 -h troup.mongohq.com:10001 -d ngc-registration -c Operations --type csv --headerline --file teman_utf8.csvi


mongo -u nirg -p dilk2d123 troup.mongohq.com:10001/ngc-registration convertDated.js

