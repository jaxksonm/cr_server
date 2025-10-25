#!/bin/bash

set -x
php -r "echo 'MCR:' . password_hash('abc123', PASSWORD_DEFAULT) . PHP_EOL;" >> users.txt
php -r "echo 'BRI:' . password_hash('finger', PASSWORD_DEFAULT) . PHP_EOL;" >> users.txt
php -r "echo 'CIR:' . password_hash('kingme', PASSWORD_DEFAULT) . PHP_EOL;" >> users.txt
php -r "echo 'COL:' . password_hash('climb14', PASSWORD_DEFAULT) . PHP_EOL;" >> users.txt
php -r "echo 'DIN:' . password_hash('silverbullet', PASSWORD_DEFAULT) . PHP_EOL;" >> users.txt
php -r "echo 'GTL:' . password_hash('callbox', PASSWORD_DEFAULT) . PHP_EOL;" >> users.txt
php -r "echo 'IMG:' . password_hash('mayhem', PASSWORD_DEFAULT) . PHP_EOL;" >> users.txt
php -r "echo 'MNL:' . password_hash('flyhigh', PASSWORD_DEFAULT) . PHP_EOL;" >> users.txt
php -r "echo 'PBP:' . password_hash('couchpoo', PASSWORD_DEFAULT) . PHP_EOL;" >> users.txt
php -r "echo 'PFW:' . password_hash('gofish', PASSWORD_DEFAULT) . PHP_EOL;" >> users.txt
php -r "echo 'QCK:' . password_hash('quackquack', PASSWORD_DEFAULT) . PHP_EOL;" >> users.txt
php -r "echo 'SPS:' . password_hash('blessyou', PASSWORD_DEFAULT) . PHP_EOL;" >> users.txt
php -r "echo 'SRR:' . password_hash('bigheadbarry', PASSWORD_DEFAULT) . PHP_EOL;" >> users.txt
php -r "echo 'SSL:' . password_hash('letsgobrandon', PASSWORD_DEFAULT) . PHP_EOL;" >> users.txt
php -r "echo 'THD:' . password_hash('hurricane', PASSWORD_DEFAULT) . PHP_EOL;" >> users.txt
php -r "echo 'TLF:' . password_hash('lowellg', PASSWORD_DEFAULT) . PHP_EOL;" >> users.txt
php -r "echo 'DOG:' . password_hash('hangten', PASSWORD_DEFAULT) . PHP_EOL;" >> users.txt
