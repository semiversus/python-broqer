from broqer.hub import Hub

hub=Hub()

hub['a'] # produce topic 'a'
hub['b.c'] # produce topic 'c' in hub 'b'
hub['b']['d'] # produce topic 'd' in hub 'b'
hub['b.e.f'] # produce topic 'f' in hub 'b.e'

# iterating over all topic paths (including recursives)
print('Listing all topic paths:')

for topic_path in hub:
  print(topic_path)

print('Listing all topic paths from b.e:')
for topic_path in hub['b.e']:
  print(topic_path)