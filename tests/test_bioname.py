from ipybd import BioName
import pytest


scientificname_split_samples = [("Syringa oblata Lindl. var. giraldii (Lemoine) Rehd. 'Chun'Ge'",
                                 ('Syringa', 'oblata', None, 'var.', 'giraldii', "(Lemoine) Rehd. 'Chun'Ge'")),
                                ('Paphiopedilum Atlantis grex', 
                                 ('Paphiopedilum', 'Atlantis', 'grex', None, None, None)),
                                ("Symphoricarpos albus (L.) S.F.Blake 'Turesson'", 
                                 ('Symphoricarpos', 'albus', None, None, None, "(L.) S.F.Blake 'Turesson'")),
                                ("Solanum tuberosum 'King Edward'", 
                                 ('Solanum', 'tuberosum', None, None, None, "'King Edward'")),
                                ('Stewartia sinensis var. acutisepala (P. L. Chiu & G. R. Zhong) T. L. Ming & J. Li ex J. L', 
                                 ('Stewartia', 'sinensis', None, 'var.', 'acutisepala', '(P. L. Chiu & G. R. Zhong) T. L. Ming & J. Li ex J. L')),
                                ('Wisteria sinensis var. multijuga auct non. Hook. f. : B. Z. Ding & S. Y. Wang',
                                 ('Wisteria', 'sinensis', None, 'var.', 'multijuga', 'auct non. Hook. f. : B. Z. Ding & S. Y. Wang')),
                                ('Trigonella emodi var. medicaginoides Širj.',
                                 ('Trigonella', 'emodi', None, 'var.', 'medicaginoides', 'Širj.')),
                                ('Pothos scandens var. sumatranus de Vriese', 
                                 ('Pothos', 'scandens', None, 'var.', 'sumatranus', 'de Vriese')),
                                ('Decaneuropsis cumingiana (Benth.)H.Rob.& Skvarla',
                                 ('Decaneuropsis', 'cumingiana', None, None, None, '(Benth.)H.Rob.& Skvarla')),
                                ('Decaneuropsis cumingiana Skvarla',
                                 ('Decaneuropsis', 'cumingiana', None, None, None, 'Skvarla')),
                                ('Narcissus enemeritoi (Sánchez-Gómez,A.F.Carrillo,A.Hern.,M.A.Carrión & '
                                 'Güemes) Sánchez-Gómez,A.F.Carrillo,A.Hernández González,M.A.Carrión & '
                                 'Güemes',
                                 ('Narcissus',
                                  'enemeritoi',
                                  None,
                                  None,
                                  None,
                                  '(Sánchez-Gómez,A.F.Carrillo,A.Hern.,M.A.Carrión & Güemes) '
                                  'Sánchez-Gómez,A.F.Carrillo,A.Hernández González,M.A.Carrión & Güemes')),
                                ('Adansonia za var. bozy (Jum. & H.Perrier) H.Perrier',
                                 ('Adansonia', 'za', None, 'var.', 'bozy', '(Jum. & H.Perrier) H.Perrier')),
                                ('Potamogeton iilinoensis var. ventanicola (Hicken) Horn af Rantzien',
                                 ('Potamogeton',
                                  'iilinoensis',
                                  None,
                                  'var.',
                                  'ventanicola',
                                  '(Hicken) Horn af Rantzien')),
                                ('Hieracium lagopus Soest non Don',
                                 ('Hieracium', 'lagopus', None, None, None, 'Soest non Don')),
                                ('Pithecellobium angulatum var. heterophylla (Roxb.) Prain, nom.nud.',
                                 ('Pithecellobium',
                                  'angulatum',
                                  None,
                                  'var.',
                                  'heterophylla',
                                  '(Roxb.) Prain, nom.nud.')),
                                ('Ania elmeri (Ames & sine ref.) A.D.Hawkes',
                                 ('Ania', 'elmeri', None, None, None, '(Ames & sine ref.) A.D.Hawkes')),
                                ('Ophrys vernixia var. regis-ferinandii (Renz) H.Baumann & al.',
                                 ('Ophrys',
                                  'vernixia',
                                  None,
                                  'var.',
                                  'regis-ferinandii',
                                  '(Renz) H.Baumann & al.')),
                                ('Lightfootia longifolia var. oppositifolia Sonder p.p.',
                                 ('Lightfootia', 'longifolia', None, 'var.', 'oppositifolia', 'Sonder p.p.')),
                                ('Bursera exequielii León de la Luz',
                                 ('Bursera', 'exequielii', None, None, None, 'León de la Luz')),
                                ('Bidens cabopulmensis León de la Luz & B.L.Turner',
                                 ('Bidens', 'cabopulmensis', None, None, None, 'León de la Luz & B.L.Turner')),
                                ('Tachigali spathulipetala L.F.Gomes da Silva, L.J.T.Cardoso, D.B.O.S.Cardoso '
                                 '& H.C.Lim',
                                 ('Tachigali',
                                  'spathulipetala',
                                  None,
                                  None,
                                  None,
                                  'L.F.Gomes da Silva, L.J.T.Cardoso, D.B.O.S.Cardoso & H.C.Lim')),
                                ('Convolvulus tricolor subsp. cupanianus (Sa ad) Stace',
                                 ('Convolvulus', 'tricolor', None, 'subsp.', 'cupanianus', '(Sa ad) Stace')),
                                ('Calea aldamoides G.H.L. da Silva, Bringel & A.M.Teles',
                                 ('Calea',
                                  'aldamoides',
                                  None,
                                  None,
                                  None,
                                  'G.H.L. da Silva, Bringel & A.M.Teles')),
                                ('Adiantum thalictroides var. hirsutum (Hook. & Grev.) de la Sota',
                                 ('Adiantum',
                                  'thalictroides',
                                  None,
                                  'var.',
                                  'hirsutum',
                                  '(Hook. & Grev.) de la Sota')),
                                ('Acianthera oricola (H.Stenzel) Karremans, Chiron & Van den Berg',
                                 ('Acianthera',
                                  'oricola',
                                  None,
                                  None,
                                  None,
                                  '(H.Stenzel) Karremans, Chiron & Van den Berg')),
                                ('Reseda urnigera var. boissieri (Müll.Arg.) Abdallah & de Wit',
                                 ('Reseda',
                                  'urnigera',
                                  None,
                                  'var.',
                                  'boissieri',
                                  '(Müll.Arg.) Abdallah & de Wit')),
                                ('Cereus auratus var. intermedius Regel & Klein bis',
                                 ('Cereus', 'auratus', None, 'var.', 'intermedius', 'Regel & Klein bis')),
                                ('Mitrophyllum articulatum (L.Bolus) de Boer ex H.Jacobsen',
                                 ('Mitrophyllum',
                                  'articulatum',
                                  None,
                                  None,
                                  None,
                                  '(L.Bolus) de Boer ex H.Jacobsen')),
                                ('Ulex parviflorus subsp. willkommii (Webb) Borja & al.',
                                 ('Ulex', 'parviflorus', None, 'subsp.', 'willkommii', '(Webb) Borja & al.')),
                                ('Lycopodioideae W.H.Wagner & Beitel ex B.Øllg.',
                                 ('Lycopodioideae', None, None, None, None, 'W.H.Wagner & Beitel ex B.Øllg.')),
                                ('Polygala paludosa var. myurus A.St.-Hil. in A.St.-Hil., Juss. & Cambess.',
                                 ('Polygala',
                                  'paludosa',
                                  None,
                                  'var.',
                                  'myurus',
                                  'A.St.-Hil. in A.St.-Hil., Juss. & Cambess.')),
                                ('Phyllostachys nigra var. stauntonii (Munro) Keng f. ex Q.F.Zheng & Y.M.Lin',
                                 ('Phyllostachys',
                                  'nigra',
                                  None,
                                  'var.',
                                  'stauntonii',
                                  '(Munro) Keng f. ex Q.F.Zheng & Y.M.Lin')),
                                ('Salix cordata var. angustifolia Zabel in Beissn., Schelle & Zabel',
                                 ('Salix',
                                  'cordata',
                                  None,
                                  'var.',
                                  'angustifolia',
                                  'Zabel in Beissn., Schelle & Zabel')),
                                ('Tsugaxpicea hookeriana (A.Murray bis) M.Van Campo-Duplan and H.Gaussen',
                                 ('Tsugaxpicea',
                                  'hookeriana',
                                  None,
                                  None,
                                  None,
                                  '(A.Murray bis) M.Van Campo-Duplan and H.Gaussen')),
                                ('Centaurea biokorensis Teyber amend.Radic',
                                 ('Centaurea', 'biokorensis', None, None, None, 'Teyber amend.Radic')),
                                ('Elaeagnus lanceolata Warb. apud',
                                 ('Elaeagnus', 'lanceolata', None, None, None, 'Warb. apud')),
                                ('Ocotea caesariata van der Werff',
                                 ('Ocotea', 'caesariata', None, None, None, 'van der Werff')),
                                ('Aiouea palaciosii (van der Werff) R.Rohde',
                                 ('Aiouea', 'palaciosii', None, None, None, '(van der Werff) R.Rohde')),
                                ('Saxifraga rufescens bal f. f.',
                                 ('Saxifraga', 'rufescens', None, None, None, 'bal f. f.')),
                                ('Saxifraga rufescens Bal f. f. var. uninervata J. T. Pan',
                                 ('Saxifraga', 'rufescens', 'Bal f. f.', 'var.', 'uninervata', 'J. T. Pan')),
                                ('Bulbophyllum nigricans (Aver.) J.J.Verm., Schuit. & de Vogel',
                                 ('Bulbophyllum',
                                  'nigricans',
                                  None,
                                  None,
                                  None,
                                  '(Aver.) J.J.Verm., Schuit. & de Vogel')),
                                ('Dactyloctenium mucronatum var. contractum Nees in Seem.',
                                 ('Dactyloctenium',
                                  'mucronatum',
                                  None,
                                  'var.',
                                  'contractum',
                                  'Nees in Seem.')),
                                ('Microcephala discoidea var. discoidea (Ledeb.) K.Bremer, H.Eklund, '
                                 'Medhanie, Heiðm., N.Laurent, Maad, Niklasson & A.Nordin',
                                 ('Microcephala',
                                  'discoidea',
                                  None,
                                  None,
                                  None,
                                  '(Ledeb.) K.Bremer, H.Eklund, Medhanie, Heiðm., N.Laurent, Maad, Niklasson '
                                  '& A.Nordin')),
                                ('Afzelia xylocarpa (Kurz) Cra',
                                 ('Afzelia', 'xylocarpa', None, None, None, '(Kurz) Cra')),
                                ('Passiflora × alatocaerulea Lindl.',
                                 ('Passiflora', '× alatocaerulea', None, None, None, 'Lindl.')),
                                ('Convolvulus ×turcicus nothosubsp. peshmenii (C.Aykurt & Sümbül) ined.',
                                 ('Convolvulus',
                                  '× turcicus',
                                  None,
                                  'subsp.',
                                  'peshmenii',
                                  '(C.Aykurt & Sümbül) ined.')),
                                ('Betula ×piperi Britton, pro spec. & C.L.Hitchc.',
                                 ('Betula', '× piperi', None, None, None, 'Britton, pro spec. & C.L.Hitchc.')),
                                ('Aster ×versicolor Willd.(pro sp.)',
                                 ('Aster', '× versicolor', None, None, None, 'Willd.(pro sp.)')),
                                ('Sapium chihsinianum S．lee',
                                 ('Sapium', 'chihsinianum', None, None, None, 'S．lee')),
                                ('Opithandra dalzielii (W.W.S.mit',
                                 ('Opithandra', 'dalzielii', None, None, None, '(W.W.S.mit')),
                                ('Opithandra dalzielii (W.W.S.mit)',
                                 ('Opithandra', 'dalzielii', None, None, None, '(W.W.S.mit)')),
                                ('Sycopsis salicifolia Li apud Wa',
                                 ('Sycopsis', 'salicifolia', None, None, None, 'Li apud Wa')),
                                ('Plumeria cv. Acutifolia',
                                 ('Plumeria cv. Acutifolia', None, None, None, None, None)),
                                ('Phegopteris decursive-pinnata (van Hall)',
                                 ('Phegopteris', 'decursive-pinnata', None, None, None, '(van Hall)')),
                                ('Eurya handel-mazzettii Hung T. Chang',
                                 ('Eurya', 'handel-mazzettii', None, None, None, 'Hung T. Chang')),
                                ('Saxifraga umbellulata Hook. f. et Thoms. var. pectinata (C. Marq. et Airy '
                                 'Shaw) J. T. Pan',
                                 ('Saxifraga',
                                  'umbellulata',
                                  'Hook. f. et Thoms.',
                                  'var.',
                                  'pectinata',
                                  '(C. Marq. et Airy Shaw) J. T. Pan')),
                                ('Cerasus pseudocerasus (Lindl.)G.Don',
                                 ('Cerasus', 'pseudocerasus', None, None, None, '(Lindl.)G.Don')),
                                ('Anemone demissa Hook. f. et Thoms. var. yunnanensis Franch.',
                                 ('Anemone',
                                  'demissa',
                                  'Hook. f. et Thoms.',
                                  'var.',
                                  'yunnanensis',
                                  'Franch.')),
                                ('Schisandra grandiflora (Wall.) Hook. f. et Thoms.',
                                 ('Schisandra',
                                  'grandiflora',
                                  None,
                                  None,
                                  None,
                                  '(Wall.) Hook. f. et Thoms.')),
                                ('Phaeonychium parryoides (Kurz ex Hook. f. et T. Anderson) O. E. Schulz',
                                 ('Phaeonychium',
                                  'parryoides',
                                  None,
                                  None,
                                  None,
                                  '(Kurz ex Hook. f. et T. Anderson) O. E. Schulz')),
                                ('Crucihimalaya lasiocarpa (Hook. f. et Thoms.) Al-Shehbaz et al.',
                                 ('Crucihimalaya',
                                  'lasiocarpa',
                                  None,
                                  None,
                                  None,
                                  '(Hook. f. et Thoms.) Al-Shehbaz et al.')),
                                ('Lindera pulcherrima (Nees) Hook. f. var. attenuata C. K. Allen',
                                 ('Lindera',
                                  'pulcherrima',
                                  '(Nees) Hook. f.',
                                  'var.',
                                  'attenuata',
                                  'C. K. Allen')),
                                ('Polygonum glaciale (Meisn.) Hook. f. var. przewalskii (A. K. Skvortsov et '
                                 'Borodina) A. J. Li',
                                 ('Polygonum',
                                  'glaciale',
                                  '(Meisn.) Hook. f.',
                                  'var.',
                                  'przewalskii',
                                  '(A. K. Skvortsov et Borodina) A. J. Li')),
                                ('Psilotrichum ferrugineum (Roxb.) Moq. var. ximengense Y. Y. Qian',
                                 ('Psilotrichum',
                                  'ferrugineum',
                                  '(Roxb.) Moq.',
                                  'var.',
                                  'ximengense',
                                  'Y. Y. Qian')),
                                ('Houpoëa officinalis (Rehd. et E. H. Wils.) N. H. Xia et C. Y. Wu',
                                 ('Houpoëa',
                                  'officinalis',
                                  None,
                                  None,
                                  None,
                                  '(Rehd. et E. H. Wils.) N. H. Xia et C. Y. Wu')),
                                ('Rhododendron delavayi Franch.',
                                 ('Rhododendron', 'delavayi', None, None, None, 'Franch.')),
                                ('Rhodododendron', (
                                 'Rhodododendron', None, None, None, None, None)),
                                ('Fabaceae', ('Fabaceae', None,
                                 None, None, None, None)),
                                ('Lindera sinisis var. nssi Franch.',
                                 ('Lindera', 'sinisis', None, 'var.', 'nssi', 'Franch.')),
                                ('Poa annua subsp. sine', (
                                 'Poa', 'annua', None, 'subsp.', 'sine', None)),
                                ('Poa annua', ('Poa', 'annua',
                                 None, None, None, None)),
                                ('Poa annua annua', (
                                 'Poa', 'annua', None, None, None, None)),
                                ('Poa annua annua (Kurz ex Hook. f. et T. Anderson) O. E. Schulz',
                                 ('Poa',
                                  'annua',
                                  None,
                                  None,
                                  None,
                                  '(Kurz ex Hook. f. et T. Anderson) O. E. Schulz')),
                                ('Rhododendron delavayi Franch.',
                                 ('Rhododendron', 'delavayi', None, None, None, 'Franch.'))]

# write a pytest test for the instance method format_latin_names of the BioName Class
@pytest.mark.parametrize("scientific_name, correct_split_name", scientificname_split_samples)
def test_split_name(scientific_name, correct_split_name):
    split_name = BioName([scientific_name]).format_latin_names('fullPlantSplitName')
    assert split_name[0] == correct_split_name 


# create a list of tuples with the non-ascii author names and the correct ascii author names
scientificname_authorship_samples = [('Hook. f.', 'Hook. f.'),
                                 ('(Wall.) Hook. f. et Thoms.', '(Wall.) Hook. f. et Thoms.'),
                                 ('H.Lév.', 'H.Lev.'),
                                 ('ßæØøþðƉłđıРТé', 'ssaeOothdDldiRTe'),
                                 ('ßæØøþðƉłđıРТé的', 'ssaeOothdDldiRTe'),
                                 ('ÆØÞÐĦĲĿŁŊŒ�', 'AEOThDHIJLLngOE')
                                 ]
# use the parametrize decorator to test the instance method ascii_authors of the BioName class
@pytest.mark.parametrize('authorship, correct_authorship', scientificname_authorship_samples)
def test_ascii_authors(authorship, correct_authorship):
    instance = BioName([])
    ascii_authorship = instance.ascii_authors(authorship)
    assert ascii_authorship == correct_authorship 

# create a list of tuples with the authorship and the correct author team
scientificname_author_team_samples = [('Hook. f.', [['Hook. f.',]]),
                                  ('(Wall.) Hook. f. et Thoms.', [['Wall.'], ['Hook. f.', 'Thoms.'], None]),
                                  ('H.Lév.', [['H.Lev.']]),
                                  ('(Benth.)H.Rob.& Skvarla', [['Benth.'], ['H.Rob.', 'Skvarla'], None]),
                                  ('Sánchez-Gómez,A.F.Carrillo,A.Hern.,M.A.Carrión & Güemes',[['Sanchez-Gomez', 'A.F.Carrillo', 'A.Hern.', 'M.A.Carrion', 'Guemes']]),
                                  ('(H.Stenzel) Karremans, Chiron & van den Berg', [['H.Stenzel'], ['Karremans', 'Chiron', 'van den Berg'], None]),
                                  ('Willd.(pro sp.)', [['Willd.']]),
                                  ('(Hook. & Grev.) de la Sota', [['Hook.', 'Grev.'], ['de la Sota'], None]),
                                  ('(Ames & sine ref.) A.D.Hawkes', [['Ames'], ['A.D.Hawkes'], None]),
                                  ('Sonder p.p.', [['Sonder']]),
                                  ('(Hook. f. et Thoms.) Al-Shehbaz et al.', [['Hook. f.', 'Thoms.'], ['Al-Shehbaz'], None]),
                                  ('(Kurz ex Hook. f. et T. Anderson) O. E. Schulz', [['Kurz'], ['Hook. f.', 'T. Anderson'], ['O. E. Schulz'], None]),
                                  ('Kurz ex Hook. f. et T. Anderson', [None, ['Kurz'], ['Hook. f.', 'T. Anderson']]),
                                  ('A.St.-Hil. in A.St.-Hil., Juss. & Cambess.', [['A.St.-Hil.']]),
                                  ('(Bruch in De Not.) Giac.', [['Bruch'], ['Giac.'], None]),
                                  ('(C.Aykurt & Sümbül) ined.', [['C.Aykurt', 'Sumbul']]),
                                  ('Regel & Klein bis', [['Regel', 'Klein bis']]),
                                  ('(Roxb.) Prain, nom.nud.', [['Roxb.'], ['Prain'], None]),
                                  ('(Desv.) de Wet & J.R.Harlan ex Davidse', [None, ['Desv.'], ['de Wet', 'J.R.Harlan'], ['Davidse']]),
                                  ('Zabel in Beissn., Schelle & Zabel', [['Zabel']]),
                                  ('C.C.Chang 1935 non Jacq. 1768', [['C.C.Chang']]),
                                  ('(Bedd. ex C.B.Clarke & Baker) Ching', [['Bedd.'], ['C.B.Clarke', 'Baker'], ['Ching'], None])
                                  ]
# use the parametrize decorator to test the instance method get_author_team of the BioName class
@pytest.mark.parametrize('authorship, correct_author_team', scientificname_author_team_samples)
def test_get_author_team(authorship, correct_author_team):
    instance = BioName([])
    author_team = instance.get_author_team(authorship, nested=True)
    assert author_team == correct_author_team



# use the parametrize decorator to test the instance method get_similar_degreen of the BioName class

# set four different degrees of authorship similarity => L: low, H: high, M: medium, S: same, E:error
# 3: they are the same authorships
# 2: some authors cannot be found in one of the authorships
# 1: some authors are different in each others
# 0: the auhtorships may come from different names or at least one of the names is wrong, 
#    this would make the mapping relationship between the names untenable
# -1: error authorship

# the model of scientific name similarity:

# a => a
  # if a => S => S
  # if a => H => H
  # if a => M => M
  # if a => L => L

# a => (b)a
  # if a => S,H,M => M
  # if a => L => L
# a => (a)b 
  # if a => S,H,M,L => L
# a => (a)a => M


# (a)b => (a)b
  # if (a)b => (S)S => S
  # if (a)b => (S)H => H
  # if (a)b => (H)S => H
  # if (a)b => (H)H => H
  # if (a)b => (S)M => M
  # if (a)b => (H)M => M
  # if (a)b => (M)M => M
  # if (a)b => (M)S => M
  # if (a)b => (M)H => M
# (a)b => (b)a
# (a)b => (a)c
# (a)b => (c)a
# (a)b => (c)b
# (a)b => (b)c
  # if (a)b => (H)L => L
  # if (a)b => (S)L => L
  # if (a)b => (M)L => L
  # if (a)b => (L)S => L
  # if (a)b => (L)H => L
  # if (a)b => (L)M => L
  # if (a)b => (L)L => L


# a ex b => (n)m => L

# a ex b => a
  # if a => S,H,M => M
  # if a => L => L
# a ex b => b
  # if b => S => S
  # if b => H => H
  # if b => M => M
  # if b => L => L
# a ex b => c
  # if b => c => M => M
  # if b => c => H => M

# a ex b => a ex b
  # if a ex b => S ex S => S
  # if a ex b => H ex S => S
  # if a ex b => M ex S => H
  # if a ex b => S ex H => H
  # if a ex b => H ex H => H
  # if a ex b => S ex M => M
  # if a ex b => H ex M => M
  # if a ex b => M ex H => M
  # if a ex b => M ex M => M
# a ex b => b ex a
# a ex b => a ex c
# a ex b => c ex a
# a ex b => c ex b
# a ex b => b ex c
  # if a ex b => S ex L => L
  # if a ex b => H ex L => L
  # if a ex b => M ex L => L
  # if a ex b => L ex S => L
  # if a ex b => L ex H => L
  # if a ex b => L ex M => L
  # if a ex b => L ex L => L

# create a list of tuples with the authorship and the simlar authorship
similar_authorship_samples = [
                           ('Y.C.Tang', 'Y.C.Tong', 3),
                          ('(Bak.) H.Iot', '(Baker) H.Itô', 3),
                          ('B.N.Chamg et al.', 'K.I.B. & K.I.M. ex B.N.Chang', 0),
                          ('L.', 'Duchesne ex Lam.', 0),
                          ('P.C.Li et Ni', 'P.C.Li & C.C.Ni', 3),
                          ('P.C.Li & C.C.Ni', 'P.C.Li et Ni', 3),
                          ('Tang & F.T.Wang', 'Tang & Lang', 1), # Wang 与 Tang 的相似度要大于与 F. T. Wang 的相似度，程序先获取相似度最大的名字，再做判断可能会导致这里 Wang 无法找到任何匹配
                          ('Tang & F.T.Wang', 'Tang & Wang', 3), # Wang 与 Tang 的相似度要大于与 F. T. Wang 的相似度，程序先获取相似度最大的名字，再做判断可能会导致这里 Wang 无法找到任何匹配
                          ('(S.G.Haw & L.A.Lauener) T.Hong & J.J.Li ex D.Y.Hong', '(S.G.Haw & Lauener) T.Hong & J.J.Li', 1), # 这里 T. Hong 与 D.Y.Hong 会被判断为同一个人
                          ('C.Chr.', 'Christ', 0), # Adiantum pedatum var. glaucinum Christ, Adiantum pedatum var. glaucinum C.Chr. 不是一个名字，这里可能会粗无的判断为命名人错误
                          ('(Bedd.) Baker', '(Bedd.) C.B.Clarke', 3),
                          ('(Wall. ex Milde) Á. Löve & D. Löve', '(Wall.) Á.Löve & D.Löve', 1),
                          ('(Wall. ex Milde) A. Love & D. Love', '(Wall.) Á.Love & D.Love', 1),
                          ('C. B. Clarke ex J. D. Hooker', 'C.B.Clarke ex Hook.f.', 3),
                          ('(A. de Candolle) G. L. Chu & M. G. Gilbert', '(A.DC.) G.L.Chu & M.G.Gilbert', 3),
                          ('(S.L. Zhou ex Landrein) Landrein', '(S.L.Zhou ex Landrein) Landrein & R.L.Barrett', 2),
                          ('(Airy Shaw) Z.H. Chen,  X.F.et P.L. Chiu Jin', '(Airy Shaw) Z.H.Chen, X.F.Jin & P.L.Chiu', 1),
                          ('Thunb. ex Murray', 'Thunb.', 1),
                          ('(Brid.) B.S.G.', '(Brid.) Bruch & Schimp.', 0),
                          ('(Dunn) Li', '(Dunn) H.L.Li', 3),
                          ('Thunb. ex Murray', 'Murray', 3),
                          ('(Wall.) Hook. f. et Thoms.', 'Wall.', 0),
                          ('(Wall.) Hook. f. et Thoms.', '(Wall.) Thoms.', 2),
                          ('(Wall.) Hook. f. et Thoms.', 'Hook. & Thoms.', 1),
                          ('(Wall.) Hook. f. et Thoms.', '(Wall.) Hook. f.', 2),
                          ('(H.Magn.) N.S.Golubk.', '(H.Magn.) J.C.Wei', 0),
                          ('(Hayata) Ching', '(Hayata) Ching ex S.H.Wu', 1),
                          ('Ching ex S.H.Wu', 'Ching', 1),
                          ('Ching et S.K.Wu', '(Sledge) Ching & S.K.Wu', 1),
                          ('(Brause) Hieron', 'Brause', 0),
                          ('(Presl) Underw.', '(Hook.) Underw.', 0),
                          ('C.Y.Wu ex C.C.Hu', '(W.W.Sm.) C.Y.Wu & C.C.Hu', 0),
                          ('W.W.Sm. & C.Y.Wu ex C.C.Hu', '(W.W.Sm.) C.Y.Wu & C.C.Hu', 0),
                          ('C.Y.Wu ex C.C.Hu', 'W.W.Sm. & C.Y.Wu & C.C.Hu', 1),
                          ('Ching et S.H.Wu', 'Ching', 2),
                          ('(Hayata) Ching', '(Hayata) Ching et S.H.Wu', 2),
                          ('H.Lev.', 'H.Lév. & Vaniot', 2),
                          ('H.W.Li', 'H.W.Li & S.K.Chen', 2),
                          ('(Ching) Ching et Y.X.Lin', '(Ching) Y.X.Lin', 2),
                          ('(Bedd. ex Clarke et Bak.) Ching', '(Bedd. ex C.B.Clarke & Baker) Ching', 3),
                          ('(Bedd. ex Clarke et Bak.) Ching', '(Bedd. ex C.B.Clarke) Ching', 2),
                          ('(Bedd. ex Clarke) Ching', '(Bedd. ex C.B.Clarke & Baker) Ching', 2),
                          ('(Clarke et Bak.) Ching', '(Bedd. ex C.B.Clarke & Baker) Ching', 3),
                          ('(Clarke) Ching', '(Bedd. ex C.B.Clarke & Baker) Ching', 2),
                          ('(Bedd.) Ching', '(Bedd. ex C.B.Clarke) Ching', 1),
                          ('Thunberg', 'Thunb.', 3),
                          ('Thunberg', 'Thunb.', 3),
                          ('(Mart. et Galeot.) Ching', '(M.Martens & Galeotti) Ching', 3)]

@pytest.mark.parametrize("authorship1, authorship2, correct_degreen", similar_authorship_samples)
def test_get_similar_degree(authorship1, authorship2, correct_degreen):
    instance = BioName([])
    authors_group1 = instance.get_author_team(authorship1, nested=True)
    authors_group2 = instance.get_author_team(authorship2, nested=True)
    degreen = instance.get_similar_degree(authors_group1, authors_group2)
    assert degreen == correct_degreen




