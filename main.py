from ReferencesReader import ReferencesReader

reader = ReferencesReader(r'./PDF_data','[0054] [Eurographics 2004] Spherical Harmonic Gradients for Mid-Range Illumination.pdf')
print(reader.min_y,reader.max_y)
print(reader)