from lib.text_opetations import text_confidence

s = '0000P11-0610-017-5-\n'.strip()

if s[-1] == '-':
    s = s[:-1]

s = s[-14:]
print(s)

print(text_confidence('иголя', 'июля'))
