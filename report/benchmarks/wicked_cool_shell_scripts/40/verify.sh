grep "bob" /etc/passwd || echo "sh failed - passwd" >result_error
grep "bob" /etc/shadow || echo "sh failed - shadow" >result_error
grep "bob" /etc/group || echo "sh failed - group" >result_error
ls /home/bob || echo "sh failed - homedir" >result_error


grep "alice" /etc/passwd || echo "hs failed - passwd" >result_error
grep "alice" /etc/shadow || echo "hs failed - shadow" >result_error
grep "alice" /etc/group || echo "hs failed - group" >result_error
ls /home/alice || echo "hs failed - homedir" >result_error
