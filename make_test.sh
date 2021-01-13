#!/bin/bash

rm -rf test_dir1
rm -rf test_dir2

mkdir test_dir1
cd test_dir1
echo "a" > a.txt
touch -a -m -t "202101102102" a.txt
echo "b" > b.txt
touch -a -m -t "202101102102" b.txt
echo "c" > c.txt
touch -a -m -t "202101102103" c.txt
echo "d" > d.txt
touch -a -m -t "202101102103" d.txt
echo "e" > e.txt
touch -a -m -t "202101102103" e.txt
for i in {1..10}
do
   dd if=/dev/zero of="big$i.dat"  bs=24M  count=1
done
cd ..

mkdir test_dir2
cd test_dir2

# no a.txt

# a newer version of b.txt, same size and content
echo "b" > b.txt
touch -a -m -t "202101102103" b.txt

# an older version of c.txt, same size and content
echo "c" > c.txt
touch -a -m -t "202101102102" c.txt

# files with identical timestmp and size but different content
echo "D" > d.txt
touch -a -m -t "202101102103" d.txt

# files with identical timestmp but different size
echo "ee" > e.txt
touch -a -m -t "202101102103" e.txt

# a file not present in the origin
echo "x" > x.txt