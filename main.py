from ReferencesReader import ReferencesReader
import crawler
import time

reader = ReferencesReader(r'./PDF_data','Liu_Invertible_Denoising_Network_A_Light_Solution_for_Real_Noise_Removal_CVPR_2021_paper.pdf')
print(reader)
# for x in reader:
#     print(x)
#     bib=crawler.get_bib_from_baiduxueshu(x)
#     print(bib)
#     time.sleep(3)
#     print()