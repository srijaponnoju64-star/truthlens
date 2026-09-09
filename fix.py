 import os

files = [
    'app/services/text_service.py',
    'app/services/image_service.py',
    'app/services/fusion_service.py'
]

for f in files:
    if os.path.exists(f):
        c = open(f).read()
        c = c.replace('llama-3.3-70b-versatile', 'llama3-70b-8192')
        c = c.replace('meta-llama/llama-4-scout-17b-16e-instruct', 'llama-3.2-11b-vision-preview')
        open(f, 'w').write(c)
        print('Fixed:', f)
    else:
        print('NOT FOUND:', f)

print('ALL DONE')
