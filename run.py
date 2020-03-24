from PIL import Image, ImageDraw, ImageFont, ImageFile
from reportlab.pdfgen import canvas
from PyPDF2 import PdfFileWriter, PdfFileReader
import unicodedata, glob, os, csv, re, textwrap, time, copy

ImageFile.LOAD_TRUNCATED_IMAGES = True

sunsetboulevard = ImageFont.truetype("static/fonts/SunsetBoulevard.otf", size=138)
sunsetboulevard_small = ImageFont.truetype("static/fonts/SunsetBoulevard.otf", size=100)
basicfont = ImageFont.truetype("static/fonts/BiryaniBold.ttf", size=50)
boldfont = ImageFont.truetype("static/fonts/ArchivoBlack.ttf", size=75)

flag = Image.open("static/images/flag.png", "r")
# f = open("missing.csv","w", encoding="utf-8")

pass_width = 839
pass_height = 1193

def clean_name(name):
    nfkd = unicodedata.normalize('NFKD', re.sub(r'[^\w\/\\\.]', '', name).lower())
    new_name = nfkd.encode('ASCII', 'ignore').decode("utf-8")
    return new_name

def clean_filenames():
    for filename in glob.iglob('variables/images/*/*', recursive=True):
        try:
            os.rename(filename, clean_name(filename))
        except:
            print("Duplicate image " + filename)
            
def gen_pdf(name, front, back):
    c = canvas.Canvas(name + '.pdf')
    c.setPageSize((pass_width, pass_height))
    c.drawImage(front, 0, 0)
    c.showPage()
    c.setPageSize((pass_width, pass_height))
    c.drawImage(back, 0, 0)
    c.save()

def draw_name(draw, x, y, fill, shadow_fill, text, w):
    lines = textwrap.wrap(text, width=w)
    y_text = y
    for line in lines:
        width, height = basicfont.getsize(line)
        draw.text((x - (width) / 2 - 1, y_text + 1), line, font=basicfont, fill=shadow_fill)
        draw.text((x - (width) / 2, y_text), line, font=basicfont, fill=fill)
        y_text += height

def draw_image(generated, picture, width, height, size):
    max_size = size
    border_size = 10
    pic_size = max_size - border_size

    picture = picture.convert("RGBA")

    pic_w, pic_h = picture.size

    if pic_w > pic_h:
        adjusted_size = int(pic_h / (pic_w/pic_size))
        picture = picture.resize((pic_size,adjusted_size), Image.ANTIALIAS)
    else:
        adjusted_size = int(pic_w / (pic_h/pic_size))
        picture = picture.resize((adjusted_size,pic_size), Image.ANTIALIAS)

    pic_w, pic_h = picture.size
    bg = Image.new('RGBA', (pic_w, pic_h), (255,255,255,255))
    border = Image.new('RGBA', (pic_w + border_size, pic_h + border_size), (240,240,240,255))
    bord_w, bord_h = border.size

    generated.paste(border, (width - (bord_w//2) ,height - (bord_h//2)))
    generated.paste(bg, (width - (pic_w//2) ,height - (pic_h//2)))
    generated.paste(picture, (width - (pic_w//2) ,height - (pic_h//2)), picture)

def search_image(path):
    found = 0

    path = clean_name(path)

    for ext in ['jpeg', 'jpg', 'png']:
        src = path + "." + ext
        if os.path.isfile(src):
            picture = Image.open(src, "r")
            found = 1
            break
    
    if found == 0:
        print("Missing image " + path)
        picture = Image.open("static/images/no_image.png", "r")

    return picture

def gen_pass(path, name, additional = { "red" : True }):
    print("Generating pass for " + name)
    if path == "csapatok" and additional['red']:
        bg = Image.open("static/images/bg_" + path + "_piros" + ".png", "r")
    else:
        bg = Image.open("static/images/bg_" + path + ".png", "r")
    
    generated = copy.deepcopy(bg)
    
    picture = search_image("variables/images/" + path + "/" + name)

    draw_image(generated, picture, 460, 500, 560)

    generated.paste(flag, (0,0), flag)

    draw = ImageDraw.Draw(generated)

    if path == "szervezteam" or path == "koordinatorok":
        title = "SZERVEZTEAM"
        draw.text((208, 728), title, fill="rgb(237,64,100)", font=sunsetboulevard)
        
        back_bg = Image.open("static/images/bg_back.jpg", "r")

    if path == "szervezteam":
        draw_name(draw, 540, 862, "rgb(34,30,66)", "rgb(255,255,255)", name, 15)

    if path == "koordinatorok":
        title = "KOORDINÁTOR"
        draw.text((310, 848), title, fill="rgb(237,64,100)", font=sunsetboulevard_small)
        for height in [0, 3, 5]:
            draw.text((570, 775 + height), ".", fill="rgb(237,64,100)", font=sunsetboulevard_small)
        draw_name(draw, 540, 952, "rgb(255,255,255)", "rgb(0,0,0)", name, 15)
        

    if path == "csapatok":
        width = boldfont.getsize(additional["team"])[0]
        draw.text((440 - width/2 - 1, 748 + 1), additional["team"], fill="rgb(0,0,0)", font=boldfont)
        draw.text((440 - width/2, 748), additional["team"], fill="rgb(237,64,100)", font=boldfont)

        draw_name(draw, 540, 852, "rgb(254,203,47)", "rgb(0,0,0)", name, 15)

        back_bg = copy.deepcopy(bg)
        back_image = search_image("variables/images/klanok/" + additional["guild"])
        draw_image(back_bg, back_image, 420, 570, 700)
        

    out_name = 'output/' + path + '/' + name
    front = out_name + '_front.png'
    back = out_name + '_back.png'

    generated.save(front)
    back_bg.save(back)
    # time.sleep(0.3)
    gen_pdf(out_name, front, back)
    os.remove(front)
    os.remove(back)



def parse_csv(path):
    with open("variables/csv/" + path + ".csv", "r", encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        index = 0
        for row in csv_reader:
            if index > 0:
                name = row[0].strip()
                if path == "csapatok":
                    gen_pass(path, name, { "red" : row[1] == "nem", "team" : row[2], "guild" : row[3]})
                else:
                    gen_pass(path, name)
            
            index = index + 1

clean_filenames()
parse_csv("csapatok")