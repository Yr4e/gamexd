"""Plan two complete, explicitly alternative 23-tome visual sets."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/tomes/dual-sets'
BASE='''Use case: stylized-concept. Create ONE original roguelite INVENTORY ICON replacing a passive tome book. Image 1 is a construction and pixel STYLE REFERENCE ONLY, not an object to duplicate. Image 2 is the corresponding original Megabonk tome, used ONLY for its main color family and mechanic identity: absolutely do not draw its BOOK shape. One centered coherent object, square TRUE TRANSPARENT RGBA background, complete object with generous 20% padding. Simple FLAT 2D PIXEL ART readable at32px: large deliberate square pixel clusters, approximately48 logical pixels across the longest visible dimension, broad untextured shapes, restrained18-24 color palette, maximum2-3 matte tones per material. Shallow diagonal view with a NARROW side edge only. Uniform readable visual size. No volumetric 3D lighting, no shiny white reflections, no smooth gradients, no tiny texture, no busy ornament or excessive details. One fine muted pale-gold outside rim matching the reference family, no added heavy dark sticker outline or second rim. No magic clouds, aura, particles, decorative stars, animals, monsters, eyes, faces, hands, scenery, tile, frame, watermark or ground shadow. NO TEXT, letters, numbers, labels, words or rank/suit printing. At most ONE large simple abstract central emblem; use the specified symbol and construction. Output just ONE icon, never multiple panels, sizes or alternatives.

'''

# Names belong to the specific alternative. Both always retain the same original_key.
PLANS=[
('Fleet','прыти', 'A SINGLE thin ivory card, clipped upper corners, vivid blue central panel and one large ivory double-chevron emblem. Tilt slightly left.','A flat BLUE WAX SEAL with an irregular six-lobed perimeter and one recessed double-chevron impression. No paper or ribbon.','single-card','wax'),
('Quickbeat','темпа','A FAN OF THREE blue-violet cards, ivory stepped edges, the front purple card has one broad gold ZIGZAG emblem. Clearly three distinct overlapping corners.','A short dark-violet HAND STAMP with a blue waist band, a broad shallow silver square foot, three large incised notches on the foot. Simple squat construction.','fan','stamp'),
('Breaker','натиска','ONE broad thin orange-red card, ivory border, one thick charcoal diagonal SLASH symbol. A single clipped corner. Flat card only.','A flat burnt-orange square SEAL STONE with one broad dark recessed diagonal slash and one chipped corner. Extremely shallow side plane, no handle.','single-card','stone'),
('Veil','завесы','TWO offset flat charcoal cards with slate-gray edges and one pale-gray split-crescent emblem on the front. A short dark-teal corner tie. Keep charcoal silhouette visible.','A flat dark slate LEAD SEAL, octagonal body, short charcoal cloth loop through the top and one pale-gray broken-circle impression. No chain or necklace.','paired-cards','hanging'),
('Gilded','золота','A compact THICK DECK bound by a single broad copper-orange strap. Ivory paper edge in three broad bands, amber top card with a single flat gold DISK emblem. No book spine.','A squat BRONZE SIGNET RING with a broad matte amber circular seal face, one deeply recessed ring-shaped mark and clear open finger hole. No gemstone or jewel shine.','bound-deck','signet'),
('Heart','сердца','A SINGLE warm-ivory card with a brown border and a large muted-PINK heart emblem. Simple rounded cut corners, tiny shallow edge, no writing.','A flat PINK WAX SEAL with a softly irregular scalloped perimeter, one broad recessed HEART impression, two pink shades, no glossy wax shine.','single-card','wax'),
('Repulse','отпора','A tightly spread FAN OF FOUR charcoal cards with red borders, front face has one broad red bent-bar emblem. Four chunky stepped corners, sparse card faces.','A thick charcoal wooden HAND STAMP with one red collar and a wide shallow oblong gray foot. One broad bent-bar impression visible on the foot side. No intricate engraving.','fan','stamp'),
('Keen','меткости','ONE slim rust-red card with steel-gray clipped corners and one large ivory targeting mark made of FOUR angular brackets with a blank center. No eye.','A shallow steel-gray square SEAL STONE with a rust-red inset face and four broad ivory corner-bracket cuts, blank center. One clipped corner, matte flat.','single-card','stone'),
('Rush','стремительности','TWO offset narrow OCHRE cards, ivory edges, one large white ARROWHEAD emblem on the front. A short orange top ribbon loop. Fast elongated card silhouette.','A flat ochre-gold hanging LEAD SEAL, tapered pentagonal shape, one broad ivory arrowhead impression and a short orange folded ribbon. No long dangling ribbons.','paired-cards','hanging'),
('Renewal','обновления','A PINK card deck partly sliding out of a short charcoal paper sleeve, one broad pink loop-arrow emblem on the sleeve. Exactly two visible card edges, simple open packet.','A thick charcoal SIGNET RING with one broad flat PINK oval seal face and a single deeply recessed LOOP impression. Large finger hole, matte unadorned band.','tuck-box','signet'),
('Bastion','оплота','A SINGLE slate-blue card, broad ivory edge and dark navy panel with ONE simple teal shield-shaped emblem. Flat silhouette with no bevelled jewel or embossed shine.','A flat NAVY BLUE WAX SEAL, broad angular perimeter, a single teal shield-shaped recessed impression. No ribbons, paper, extra shields or reflective metal.','single-card','wax'),
('Argent','серебра','A THIN DECK of icy-silver cards held with a broad dark-cyan band. Three ivory paper-edge bands, top face has one horizontal silver bar emblem. No glitter.','A short SILVER HAND STAMP with a simple icy-cyan squat handle and a wide flat pale-gray rectangular foot, one horizontal dark-cyan bar cut. No gloss or jewels.','bound-deck','stamp'),
('Broad','размаха','ONE unusually WIDE landscape-format amber card, ivory edges, a dark-brown center with one large gold expanding-brackets emblem. Clearly wider than tall, simple flat card.','A WIDE thin rectangular amber SEAL STONE with two opposed large dark expanding-bracket incisions, a tiny corner chip and a narrow ochre edge. No pillars or stand.','wide-card','stone'),
('Bulwark','бастиона','A blue-gray CARD TUCK BOX with its lid FLAP open and a small ivory deck protruding, one broad stepped-wall chevron on front. Three chunky folds only. Not a chest or a book.','A flat blue-gray LEAD SEAL with a hexagonal body and one simple stepped-wall emblem, suspended from a short folded ivory cloth tab. Flat construction with no armor figure.','tuck-box','hanging'),
('Lure','притяжения','TWO offset moss-green cards with copper-brown edges, a short green ribbon tie and ONE broad gold inward-curving HOOK emblem on the front. Sparse abstract symbol.','A simple COPPER SIGNET RING with a flat moss-green square face and one gold hook-shaped recessed mark. Thick plain band with a clear open hole. No emerald gemstone.','paired-cards','signet'),
('Crimson','крови','ONE slender crimson card with dark-gray clipped edges and ONE large ivory DROP emblem. Plain matte red central field, shallow thin side plane.','A flat CRIMSON WAX SEAL with an angular irregular perimeter and ONE recessed drop impression, dark-red cuts, two-tone red body. No blood splash or dripping particles.','single-card','wax'),
('Wild','хаоса','A FAN OF THREE charcoal and cyan cards, asymmetrically offset, front face has ONE simple ivory split-square emblem, only two cyan tones. No dice or random particle effects.','A squat asymmetrical charcoal HAND STAMP, one cyan handle band and a broad hexagonal cyan-gray foot with ONE split-square cut. Coherent usable stamp, no living creature.','fan','stamp'),
('Burden','бремени','A small dense burnt-AMBER DECK bound by one broad near-black strap, ivory edges in two bands, top card bears three broad dark notches as ONE emblem. No book spine or clasp.','A chunky amber-brown square SEAL STONE with three broad near-black recessed notches and one broken corner. Keep the side plane shallow and surfaces flat, no tiny cracks.','bound-deck','stone'),
('Lingering','длительности','TWO long navy cards, offset vertically and held by one short GOLD ribbon loop. Front card has ONE simple ivory hourglass emblem made from two broad triangles. No glass object.','A flat NAVY oval LEAD SEAL on a short gold ribbon, one broad ivory HOURGLASS impression made of two triangles. A single coherent seal, narrow flat edge.','paired-cards','hanging'),
('Fortune','удачи','A GREEN deck in an open brown paper sleeve, ivory card edges, one gold emblem composed of FOUR broad joined diamonds on the front. Simple square packet, no clover plant or coins.','A wide plain BRONZE SIGNET RING with a flat GREEN seal face, one cream four-diamond impression and a clear large finger hole. Matte metal, no jewels or complex filigree.','tuck-box','signet'),
('Echo','эха','A WIDE FAN OF FIVE violet cards with magenta edges. Five clear stepped corners, front card carries three large ivory discs forming ONE triangular emblem. No additional floating objects.','A flat VIOLET WAX SEAL made of two slightly overlapping wax pools as ONE connected silhouette; one simple double-disc recessed mark. Broad magenta edges, no particles.','fan','wax'),
('Thorn','шипов','ONE dark-red card with a charcoal border and one ivory three-point spike emblem, bold abstract graphic ON THE FACE, not a blade or weapon. Slightly notched paper corner.','A squat walnut HAND STAMP with a muted-red collar and one broad charcoal foot. The foot has three very short blunt teeth along one edge, chunky simple construction. Not a weapon.','single-card','stamp'),
('Insight','прозрения','A DARK TEAL card packet, top flap open to show two ivory card tops, one large rising white chevron on the front. Compact thin paper sleeve, narrow brass trim. No book, stars or writing.','A flat DARK TEAL square SEAL STONE with a single broad ivory rising-chevron incision and a narrow ochre side edge. One stepped corner, untextured matte two-tone surface.','tuck-box','stone'),
]

CARD_REFS={'single-card':1,'wide-card':1,'fan':2,'bound-deck':3,'tuck-box':4,'paired-cards':5}
SEAL_REFS={'wax':1,'stamp':2,'hanging':3,'stone':4,'signet':5}


def main():
    original=json.loads((ROOT/'assets/tomes/catalog.json').read_text(encoding='utf-8'))
    assert len(original['tomes'])==len(PLANS)==23
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'source-catalog.json').write_text(json.dumps(original,ensure_ascii=False,indent=2),encoding='utf-8')
    plan=[]
    for tome,(stem,ru,card,seal,card_type,seal_type) in zip(original['tomes'],PLANS):
        n=tome['id']
        for group,subject,shape,ref in [('cards',card,card_type,CARD_REFS[card_type]),('seals',seal,seal_type,SEAL_REFS[seal_type])]:
            folder=OUT/group
            for sub in ('prompts','raw','icons_256','data','entries','sheets'):(folder/sub).mkdir(parents=True,exist_ok=True)
            is_cards=group=='cards'
            noun='Card' if card_type in ('single-card','wide-card') else ('Fan' if card_type=='fan' else 'Deck' if card_type in ('bound-deck','tuck-box') else 'Pair')
            en=f'{stem} {noun}' if is_cards else f'{stem} Seal'
            ru_noun={'Card':'Карта','Fan':'Веер','Deck':'Колода','Pair':'Пара'}[noun] if is_cards else 'Печать'
            prompt=BASE+'Family: '+('CARDS AND DECKS' if is_cards else 'SEALS AND STAMPS')+'\nOriginal mechanic context only: '+tome['effect_label_ru']+'; '+tome['effect_source_en']+'. Do not print these words.\nSUBJECT: '+subject
            prompt_file=f'{group}/prompts/{n:02d}.txt'
            (OUT/prompt_file).write_text(prompt,encoding='utf-8')
            plan.append({'id':n,'asset_id':tome['asset_id'],'original_key':tome['original_key'],'original_name':tome['original_name'],
                         'group':group,'set_id':'tomes-'+group+'-v1','variant_id':tome['asset_id']+'@'+group+'-v1',
                         'new_name_en':en,'new_name_ru':ru_noun+' '+ru,'construction':shape,'prompt':prompt,'prompt_file':prompt_file,
                         'references':[str(ROOT/f'assets/tomes/cards-seals-01/{group}/icons_256/{ref:02d}.png'),str(ROOT/'assets/tomes'/tome['original_file'])],
                         'raw_file':f'{group}/raw/{n:02d}.png','receipt_file':f'{group}/raw/{n:02d}.json','our_file':f'{group}/icons_256/{n:02d}.png',
                         'data_file':f'{group}/data/{n:02d}.json','entry_file':f'{group}/entries/{n:02d}.html'})
    (OUT/'plan.json').write_text(json.dumps({'count':46,'selected_set':None,'stage':'two-alternative-sets','variants':plan},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Planned 46 individually generated variants for 23 original tome IDs. No default set selected.')


if __name__=='__main__':main()
