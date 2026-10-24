# Gera icone.ico / icone.png (gateway: 1 entrada -> 3 saidas) - rode se quiser recriar o icone
from PIL import Image, ImageDraw

S = 1024  # desenha grande e reduz (suaviza as bordas)
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# fundo: quadrado arredondado laranja (cor do 9router)
d.rounded_rectangle((32, 32, S - 32, S - 32), radius=220, fill=(217, 119, 87, 255))

W = (255, 255, 255, 255)
hub = (430, 512)
outs = [(800, 270), (800, 512), (800, 754)]

# linha de entrada e linhas de saida
d.line([(190, 512), hub], fill=W, width=56)
for p in outs:
    d.line([hub, p], fill=W, width=48)

# no central (o roteador) e nos de destino (provedores)
d.ellipse((hub[0] - 120, hub[1] - 120, hub[0] + 120, hub[1] + 120), fill=W)
d.ellipse((hub[0] - 58, hub[1] - 58, hub[0] + 58, hub[1] + 58), fill=(217, 119, 87, 255))
for x, y in outs:
    d.ellipse((x - 78, y - 78, x + 78, y + 78), fill=W)
d.ellipse((150, 472, 230, 552), fill=W)

img.save("icone.png")
img.save("icone.ico", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
print("ok")
