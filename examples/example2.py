from broqer.hub import Hub

hub=Hub()

hub['a'] # produce stream 'a'
hub['b.c'] # produce stream 'c' in hub 'b'
hub['b']['d'] # produce stream 'd' in hub 'b'
hub['b.e.f'] # produce stream 'f' in hub 'b.e'

# iterating over all stream paths (including recursives)
print('Listing all stream paths:')

for stream_path in hub:
  print(stream_path)

print('Listing all stream paths from b.e:')
for stream_path in hub['b.e']:
  print(stream_path)