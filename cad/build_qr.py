"""FFBeast sliding-wedge Quick Release - generator modelu dla Fusion 360.

Uruchamianie: Fusion 360 -> Utilities -> Scripts and Add-Ins -> (dodaj ten plik) -> Run,
albo przez serwer MCP Fusion (featureType="script").
Zmien wartosci w slowniku P i uruchom ponownie - skrypt zbuduje caly zespol od nowa
w nowym dokumencie.  Wszystkie wymiary w mm / stopniach.

Uklad wspolrzednych:
  Z = os kierownicy, Z=0 = czolo flanszy (strona kierownicy), +Z w strone kierowcy
  Y = kierunek wsuwania; kierownica (czesc B) wsuwa sie w kierunku -Y, w strone wiezyczki blokady
"""
import adsk.core, adsk.fusion, math

P = {
    # --- interfejs z flansza / kierownica (zmierzone z STL) ---
    'qr_dia':        (86.0, 'mm', 'Srednica zewnetrzna czesci A i B'),
    'pcd':           (70.0, 'mm', 'Srednica okregu 6 otworow (zmierzona z STL: 70.00)'),
    'a_hole_d':      (5.5,  'mm', 'Otwor przelotowy M5 w czesci A'),
    'a_cbore_d':     (10.4, 'mm', 'Poglebienie pod leb M5 ISO 7380 (leb 9.5 mm)'),
    'a_under_head':  (4.8,  'mm', 'Grubosc materialu pod lbem sruby czesci A'),
    'b_hole_d':      (5.4,  'mm', 'Otwor przelotowy M5 w czesci B'),
    'b_nut_af':      (8.3,  'mm', 'Gniazdo nakretki M5 (wymiar pod klucz 8.0 + luz)'),
    'b_nut_depth':   (6.0,  'mm', 'Glebokosc gniazda nakretki od plaszczyzny styku'),
    # --- geometria klina ---
    'a_floor':       (8.0,  'mm', 'Grubosc dna kanalu czesci A'),
    'dv_h':          (8.0,  'mm', 'Wysokosc jaskolczego ogona'),
    'b_plate':       (10.0, 'mm', 'Grubosc plyty czesci B'),
    'alpha':         (14.0, 'deg', 'Polkat klina V w planie'),
    'beta':          (35.0, 'deg', 'Podciecie jaskolczego ogona od pionu'),
    'wf_tip':        (14.0, 'mm', 'Polszerokosc kanalu przy dnie na wysokosci czubka piora'),
    'y_tip':         (-22.0, 'mm', 'Polozenie czubka piora (nominalne dosuniecie)'),
    'y_wall':        (-25.0, 'mm', 'Sciana koncowa kanalu (szczelina 3 mm = zapas na dosuniecie)'),
    'y_tail':        (24.5, 'mm', 'Tylny koniec piora'),
    'fit_clr':       (0.10, 'mm', 'Luz boczny piora na strone (kierunek X) - kalibracja pasowania'),
    'floor_gap':     (0.30, 'mm', 'Szczelina pioro / dno kanalu'),
    'r_floor':       (0.8,  'mm', 'Promien u nasady wargi czesci A'),
    'c_lip':         (1.7,  'mm', 'Faza krawedzi wargi czesci A'),
    'r_root':        (0.8,  'mm', 'Promien u nasady piora czesci B'),
    'c_tongue':      (1.2,  'mm', 'Faza dolnych krawedzi piora'),
    # --- blokada ---
    'lock_z':        (17.0, 'mm', 'Wysokosc osi sruby blokujacej'),
    'tower_hw':      (9.0,  'mm', 'Polszerokosc wiezyczki blokady'),
    'tower_top':     (25.0, 'mm', 'Gorna powierzchnia wiezyczki'),
    'y_flat':        (-42.0, 'mm', 'Plaska powierzchnia oporowa pokretla'),
    'notch_clr':     (0.7,  'mm', 'Luz wyciecia czesci B wokol wiezyczki'),
    'thr_pilot':     (9.0,  'mm', 'Otwor pod gwint wewnetrzny Tr12x3'),
    'thr_depth':     (18.0, 'mm', 'Glebokosc otworu gwintowanego w piorze'),
    'cap_len':       (5.0,  'mm', 'Dlugosc gwintu zabezpieczajacego srube przed wypadnieciem'),
    'lock_clr_d':    (11.8, 'mm', 'Otwor przelotowy sruby w wiezyczce'),
    'scr_thr_d':     (11.0, 'mm', 'Srednica gwintu sruby (Tr11x3 - celowo mniejsza niz Tr12)'),
    'scr_thr_len':   (12.0, 'mm', 'Dlugosc gwintu sruby'),
    'scr_neck_d':    (8.2,  'mm', 'Szyjka sruby'),
    'scr_pilot_d':   (7.4,  'mm', 'Pilot na czubku sruby'),
    'scr_pilot_len': (2.0,  'mm', 'Dlugosc pilota'),
    'scr_collar_d':  (16.4, 'mm', 'Kolnierz oporowy sruby'),
    'scr_collar_t':  (2.5,  'mm', 'Grubosc kolnierza'),
    'scr_wing_w':    (15.0, 'mm', 'Szerokosc skrzydelka'),
    'scr_wing_t':    (7.0,  'mm', 'Grubosc skrzydelka'),
    'scr_wing_len':  (14.0, 'mm', 'Dlugosc skrzydelka'),
}
THREAD_TYPE = 'ISO Metric Trapezoidal Threads'
THREAD_INT = ('TR12x3', '7H')
THREAD_EXT = ('TR11x3', '7e')

VI = adsk.core.ValueInput
OP = adsk.fusion.FeatureOperations


def v(k):
    return P[k][0]


def wf(y):
    """polszerokosc kanalu przy dnie (z = a_floor) w funkcji y"""
    return v('wf_tip') + (y - v('y_tip')) * math.tan(math.radians(v('alpha')))


def P3(x, y, z):
    return adsk.core.Point3D.create(x / 10.0, y / 10.0, z / 10.0)


def plane_z(comp, z, name):
    pi = comp.constructionPlanes.createInput()
    pi.setByOffset(comp.xYConstructionPlane, VI.createByReal(z / 10.0))
    pl = comp.constructionPlanes.add(pi)
    pl.name = name
    pl.isLightBulbOn = False
    return pl


def plane_y(comp, y, name):
    base = comp.xZConstructionPlane
    s = 1.0 if base.geometry.normal.y > 0 else -1.0
    pi = comp.constructionPlanes.createInput()
    pi.setByOffset(base, VI.createByReal(s * y / 10.0))
    pl = comp.constructionPlanes.add(pi)
    pl.name = name
    pl.isLightBulbOn = False
    return pl, s


def new_sketch(comp, plane, name):
    sk = comp.sketches.add(plane)
    sk.name = name
    return sk


def poly(sk, pts):
    """pts: lista (x,y,z) w mm, uklad modelu"""
    lines = sk.sketchCurves.sketchLines
    sp = [sk.modelToSketchSpace(P3(*p)) for p in pts]
    first = lines.addByTwoPoints(sp[0], sp[1])
    prev = first
    for i in range(2, len(sp)):
        prev = lines.addByTwoPoints(prev.endSketchPoint, sp[i])
    lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)


def circle(sk, c, d):
    sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P3(*c)), d / 20.0)


def all_profiles(sk):
    oc = adsk.core.ObjectCollection.create()
    for p in sk.profiles:
        oc.add(p)
    return oc


def extrude(comp, prof, dist_mm, op, name):
    ef = comp.features.extrudeFeatures
    inp = ef.createInput(prof, op)
    inp.setDistanceExtent(False, VI.createByString('%.5f mm' % dist_mm))
    if op != OP.NewBodyFeatureOperation:
        # ogranicz operacje do bryly wlasnego komponentu (inaczej ciecie trafia tez w sasiednie czesci)
        inp.participantBodies = [comp.bRepBodies.item(0)]
    f = ef.add(inp)
    f.name = name
    return f


def loft(comp, prof_a, prof_b, op, name):
    lf = comp.features.loftFeatures
    li = lf.createInput(op)
    li.loftSections.add(prof_a)
    li.loftSections.add(prof_b)
    li.isSolid = True
    if op != OP.NewBodyFeatureOperation:
        li.participantBodies = [comp.bRepBodies.item(0)]
    f = lf.add(li)
    f.name = name
    return f


def line_edges(body, z_mm, min_dy=10.0, max_absx=None):
    """proste krawedzie lezace na wysokosci z, biegnace glownie wzdluz Y"""
    oc = adsk.core.ObjectCollection.create()
    for e in body.edges:
        if e.geometry.objectType != adsk.core.Line3D.classType():
            continue
        a, b = e.startVertex.geometry, e.endVertex.geometry
        if abs(a.z * 10 - z_mm) > 1e-3 or abs(b.z * 10 - z_mm) > 1e-3:
            continue
        if abs(a.y - b.y) * 10 < min_dy:
            continue
        if max_absx is not None and max(abs(a.x), abs(b.x)) * 10 > max_absx:
            continue
        oc.add(e)
    return oc


def rim_edges(body, z_mm, r_mm):
    oc = adsk.core.ObjectCollection.create()
    for e in body.edges:
        g = e.geometry
        t = g.objectType
        if t not in (adsk.core.Arc3D.classType(), adsk.core.Circle3D.classType()):
            continue
        if abs(g.radius * 10 - r_mm) > 1e-3 or abs(g.center.z * 10 - z_mm) > 1e-3:
            continue
        if abs(g.center.x) > 1e-4 or abs(g.center.y) > 1e-4:
            continue
        oc.add(e)
    return oc


def fillet(comp, edges, r_mm, name):
    assert edges.count > 0, 'brak krawedzi dla ' + name
    ff = comp.features.filletFeatures
    fi = ff.createInput()
    fi.edgeSetInputs.addConstantRadiusEdgeSet(edges, VI.createByString('%.4f mm' % r_mm), True)
    f = ff.add(fi)
    f.name = name
    return f


def chamfer(comp, edges, d_mm, name):
    assert edges.count > 0, 'brak krawedzi dla ' + name
    cf = comp.features.chamferFeatures
    ci = cf.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, VI.createByString('%.4f mm' % d_mm), True)
    f = cf.add(ci)
    f.name = name
    return f


def cyl_face(body, r_mm, pred):
    for f in body.faces:
        g = f.geometry
        if g.objectType == adsk.core.Cylinder.classType() and abs(g.radius * 10 - r_mm) < 1e-3 and pred(f):
            return f
    raise RuntimeError('nie znaleziono powierzchni walcowej r=%s' % r_mm)


def thread(comp, face, internal, name):
    tf = comp.features.threadFeatures
    des, cls = THREAD_INT if internal else THREAD_EXT
    info = tf.createThreadInfo(internal, THREAD_TYPE, des, cls)
    ti = tf.createInput(face, info)
    ti.isFullLength = True
    ti.isModeled = True
    f = tf.add(ti)
    f.name = name
    return f


def bbox(body):
    b = body.boundingBox
    return '[%.2f..%.2f, %.2f..%.2f, %.2f..%.2f] vol=%.0f mm3' % (
        b.minPoint.x * 10, b.maxPoint.x * 10, b.minPoint.y * 10, b.maxPoint.y * 10,
        b.minPoint.z * 10, b.maxPoint.z * 10, body.volume * 1000)


def hole_positions():
    r = v('pcd') / 2.0
    return [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in range(0, 360, 60)]


def build_A(root):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    c = occ.component
    c.name = 'A_baza_QR'
    R = v('qr_dia') / 2.0
    zt = v('a_floor') + v('dv_h')          # plaszczyzna styku
    tb = math.tan(math.radians(v('beta')))

    sk = new_sketch(c, c.xYConstructionPlane, 'A_obrys')
    circle(sk, (0, 0, 0), 2 * R)
    extrude(c, sk.profiles.item(0), zt, OP.NewBodyFeatureOperation, 'A_dysk')
    body = c.bRepBodies.item(0)
    body.name = 'A_baza_QR'

    # kanal V z podcieciem: loft miedzy przekrojem przy dnie i ponad plaszczyzna styku
    yb, ye, ov = v('y_wall'), R + 8.0, 0.5
    s1 = new_sketch(c, plane_z(c, v('a_floor'), 'A_pl_dno'), 'A_kanal_dno')
    poly(s1, [(-wf(yb), yb, v('a_floor')), (wf(yb), yb, v('a_floor')), (wf(ye), ye, v('a_floor')), (-wf(ye), ye, v('a_floor'))])
    d = (v('dv_h') + ov) * tb
    s2 = new_sketch(c, plane_z(c, zt + ov, 'A_pl_gora'), 'A_kanal_gora')
    poly(s2, [(-wf(yb) + d, yb, zt + ov), (wf(yb) - d, yb, zt + ov), (wf(ye) - d, ye, zt + ov), (-wf(ye) + d, ye, zt + ov)])
    loft(c, s1.profiles.item(0), s2.profiles.item(0), OP.CutFeatureOperation, 'A_kanal_V')
    print('A po kanale', bbox(body))

    fillet(c, line_edges(body, v('a_floor')), v('r_floor'), 'A_promien_nasady_wargi')
    chamfer(c, line_edges(body, zt), v('c_lip'), 'A_faza_wargi')

    # wiezyczka blokady
    s = new_sketch(c, plane_z(c, zt, 'A_pl_styk'), 'A_wiezyczka')
    hw = v('tower_hw')
    poly(s, [(-hw, -R - 3, zt), (hw, -R - 3, zt), (hw, v('y_wall'), zt), (-hw, v('y_wall'), zt)])
    extrude(c, s.profiles.item(0), v('tower_top') - zt, OP.JoinFeatureOperation, 'A_wiezyczka')
    s = new_sketch(c, c.xYConstructionPlane, 'A_splaszczenie')
    poly(s, [(-hw - 6, -R - 6, 0), (hw + 6, -R - 6, 0), (hw + 6, v('y_flat'), 0), (-hw - 6, v('y_flat'), 0)])
    extrude(c, s.profiles.item(0), v('tower_top') + 5, OP.CutFeatureOperation, 'A_powierzchnia_oporowa')
    print('A po wiezyczce', bbox(body))

    # 6 otworow montazowych + poglebienia
    s = new_sketch(c, c.xYConstructionPlane, 'A_otwory_M5')
    for (x, y) in hole_positions():
        circle(s, (x, y, 0), v('a_hole_d'))
    extrude(c, all_profiles(s), v('tower_top') + 5, OP.CutFeatureOperation, 'A_otwory_M5')
    zu = v('a_under_head')
    s = new_sketch(c, plane_z(c, zu, 'A_pl_pod_lbem'), 'A_poglebienia')
    for (x, y) in hole_positions():
        circle(s, (x, y, zu), v('a_cbore_d'))
    extrude(c, all_profiles(s), v('tower_top') + 5, OP.CutFeatureOperation, 'A_poglebienia')

    # otwor sruby blokujacej: gwint zabezpieczajacy + otwor przelotowy
    pl, sg = plane_y(c, v('y_flat'), 'A_pl_opor')
    s = new_sketch(c, pl, 'A_otwor_gwint')
    circle(s, (0, v('y_flat'), v('lock_z')), v('thr_pilot'))
    extrude(c, s.profiles.item(0), sg * (v('y_wall') - v('y_flat') + 1.0), OP.CutFeatureOperation, 'A_otwor_pod_gwint')
    y0 = v('y_flat') + v('cap_len')
    pl, sg = plane_y(c, y0, 'A_pl_przelot')
    s = new_sketch(c, pl, 'A_otwor_przelot')
    circle(s, (0, y0, v('lock_z')), v('lock_clr_d'))
    extrude(c, s.profiles.item(0), sg * (v('y_wall') - y0 + 1.0), OP.CutFeatureOperation, 'A_otwor_przelotowy_sruby')
    f = cyl_face(body, v('thr_pilot') / 2.0, lambda f: f.boundingBox.maxPoint.y * 10 < y0 + 0.01)
    thread(c, f, True, 'A_gwint_zabezpieczajacy_Tr12x3')

    chamfer(c, rim_edges(body, 0.0, R), 0.6, 'A_faza_dol')
    chamfer(c, rim_edges(body, zt, R), 0.8, 'A_faza_gora')
    print('A gotowe', bbox(body))
    return occ


def build_B(root):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    c = occ.component
    c.name = 'B_adapter_kierownicy'
    R = v('qr_dia') / 2.0
    zt = v('a_floor') + v('dv_h')
    zb = v('a_floor') + v('floor_gap')
    ztop = zt + v('b_plate')
    tb = math.tan(math.radians(v('beta')))
    cx = v('fit_clr')

    s = new_sketch(c, plane_z(c, zt, 'B_pl_styk'), 'B_obrys')
    circle(s, (0, 0, zt), 2 * R)
    extrude(c, s.profiles.item(0), v('b_plate'), OP.NewBodyFeatureOperation, 'B_plyta')
    body = c.bRepBodies.item(0)
    body.name = 'B_adapter_kierownicy'

    # pioro V (loft od spodu piora do wnetrza plyty)
    y1, y2, ov = v('y_tip'), v('y_tail'), 0.5
    def hwz(y, z):
        return wf(y) - (z - v('a_floor')) * tb - cx
    s1 = new_sketch(c, plane_z(c, zb, 'B_pl_spod_piora'), 'B_pioro_spod')
    poly(s1, [(-hwz(y1, zb), y1, zb), (hwz(y1, zb), y1, zb), (hwz(y2, zb), y2, zb), (-hwz(y2, zb), y2, zb)])
    s2 = new_sketch(c, plane_z(c, zt + ov, 'B_pl_nasada'), 'B_pioro_nasada')
    poly(s2, [(-hwz(y1, zt + ov), y1, zt + ov), (hwz(y1, zt + ov), y1, zt + ov), (hwz(y2, zt + ov), y2, zt + ov), (-hwz(y2, zt + ov), y2, zt + ov)])
    loft(c, s1.profiles.item(0), s2.profiles.item(0), OP.JoinFeatureOperation, 'B_pioro_V')
    print('B po piorze', bbox(body))

    chamfer(c, line_edges(body, zb), v('c_tongue'), 'B_faza_spodu_piora')
    fillet(c, line_edges(body, zt), v('r_root'), 'B_promien_nasady_piora')

    # wyciecie na wiezyczke
    hw = v('tower_hw') + v('notch_clr')
    s = new_sketch(c, plane_z(c, zt, 'B_pl_styk2'), 'B_wyciecie')
    poly(s, [(-hw, -R - 5, zt), (hw, -R - 5, zt), (hw, y1, zt), (-hw, y1, zt)])
    extrude(c, s.profiles.item(0), v('b_plate') + 2, OP.CutFeatureOperation, 'B_wyciecie_na_wiezyczke')

    # otwory kierownicy + gniazda nakretek
    s = new_sketch(c, plane_z(c, zb - 1.0, 'B_pl_otwory'), 'B_otwory_M5')
    for (x, y) in hole_positions():
        circle(s, (x, y, zb - 1.0), v('b_hole_d'))
    extrude(c, all_profiles(s), ztop - zb + 3.0, OP.CutFeatureOperation, 'B_otwory_M5')
    s = new_sketch(c, plane_z(c, zt, 'B_pl_styk3'), 'B_gniazda')
    rc = v('b_nut_af') / 2.0 / math.cos(math.radians(30))
    for (x, y) in hole_positions():
        poly(s, [(x + rc * math.cos(math.radians(a)), y + rc * math.sin(math.radians(a)), zt) for a in range(0, 360, 60)])
    profs = adsk.core.ObjectCollection.create()
    for p in s.profiles:
        profs.add(p)
    extrude(c, profs, v('b_nut_depth'), OP.CutFeatureOperation, 'B_gniazda_nakretek_M5')

    # otwor gwintowany sruby blokujacej
    pl, sg = plane_y(c, y1, 'B_pl_czolo')
    s = new_sketch(c, pl, 'B_otwor_gwint')
    circle(s, (0, y1, v('lock_z')), v('thr_pilot'))
    extrude(c, s.profiles.item(0), sg * v('thr_depth'), OP.CutFeatureOperation, 'B_otwor_pod_gwint')
    f = cyl_face(body, v('thr_pilot') / 2.0, lambda f: True)
    thread(c, f, True, 'B_gwint_blokady_Tr12x3')

    chamfer(c, rim_edges(body, ztop, R), 0.6, 'B_faza_gora')
    chamfer(c, rim_edges(body, zt, R), 0.8, 'B_faza_dol')
    print('B gotowe', bbox(body))
    return occ


def build_C(root):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    c = occ.component
    c.name = 'C_sruba_blokujaca'
    z0 = v('lock_z')
    y_sh = v('y_wall')                       # koniec szyjki / poczatek gwintu (stan dokrecony)
    y_fl = v('y_flat')

    pl, sg = plane_y(c, y_sh, 'C_pl_gwint')
    s = new_sketch(c, pl, 'C_gwint')
    circle(s, (0, y_sh, z0), v('scr_thr_d'))
    extrude(c, s.profiles.item(0), sg * v('scr_thr_len'), OP.NewBodyFeatureOperation, 'C_trzpien_gwintu')
    body = c.bRepBodies.item(0)
    body.name = 'C_sruba_blokujaca'
    f = cyl_face(body, v('scr_thr_d') / 2.0, lambda f: True)
    thread(c, f, False, 'C_gwint_Tr11x3')
    # pilot na czubku (mniejszy niz srednica wewnetrzna nakretki) - ulatwia trafienie w gwint
    yt = y_sh + v('scr_thr_len')
    plt, sgt = plane_y(c, yt, 'C_pl_czubek')
    s = new_sketch(c, plt, 'C_pilot')
    circle(s, (0, yt, z0), v('scr_pilot_d'))
    extrude(c, s.profiles.item(0), sgt * v('scr_pilot_len'), OP.JoinFeatureOperation, 'C_pilot')

    s = new_sketch(c, pl, 'C_szyjka')
    circle(s, (0, y_sh, z0), v('scr_neck_d'))
    extrude(c, s.profiles.item(0), -sg * (y_sh - y_fl), OP.JoinFeatureOperation, 'C_szyjka')

    pl2, sg2 = plane_y(c, y_fl, 'C_pl_kolnierz')
    s = new_sketch(c, pl2, 'C_kolnierz')
    circle(s, (0, y_fl, z0), v('scr_collar_d'))
    extrude(c, s.profiles.item(0), -sg2 * v('scr_collar_t'), OP.JoinFeatureOperation, 'C_kolnierz')

    yw = y_fl - v('scr_collar_t')
    pl3, sg3 = plane_y(c, yw, 'C_pl_skrzydelko')
    s = new_sketch(c, pl3, 'C_skrzydelko')
    w, t = v('scr_wing_w') / 2.0, v('scr_wing_t') / 2.0
    poly(s, [(-w, yw, z0 - t), (w, yw, z0 - t), (w, yw, z0 + t), (-w, yw, z0 - t + 2 * t)])
    extrude(c, s.profiles.item(0), -sg3 * v('scr_wing_len'), OP.JoinFeatureOperation, 'C_skrzydelko')

    # plaska powierzchnia do druku na lezaco (spod skrzydelka = plaszczyzna stolu)
    yc = yw - v('scr_wing_len') - 2.0
    pl4, sg4 = plane_y(c, yc, 'C_pl_ciecie')
    s = new_sketch(c, pl4, 'C_plaska_do_druku')
    poly(s, [(-15, yc, z0 - 15), (15, yc, z0 - 15), (15, yc, z0 - t), (-15, yc, z0 - t)])
    extrude(c, s.profiles.item(0), sg4 * 60.0, OP.CutFeatureOperation, 'C_plaska_do_druku')
    print('C gotowe', bbox(body))
    return occ


def run(_context: str):
    app = adsk.core.Application.get()
    for d in [d for d in app.documents]:
        prod = d.products.itemByProductType('DesignProductType')
        if prod and prod.attributes.itemByName('ffbeast_qr', 'generated'):
            d.close(False)
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    des = adsk.fusion.Design.cast(app.activeProduct)
    des.designType = adsk.fusion.DesignTypes.ParametricDesignType
    des.attributes.add('ffbeast_qr', 'generated', '1')
    root = des.rootComponent
    for k, (val, unit, comment) in P.items():
        try:
            des.userParameters.add('qr_' + k if not k.startswith('qr_') else k, VI.createByString('%s %s' % (val, unit)), unit, comment)
        except RuntimeError as e:
            raise RuntimeError('parametr %s: %s' % (k, e))
    build_A(root)
    build_B(root)
    build_C(root)
    bad = []
    for i in range(des.timeline.count):
        it = des.timeline.item(i)
        if it.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:
            bad.append('%s: %s' % (it.name, it.errorOrWarningMessage))
    for comp in des.allComponents:
        if comp != root:
            print(comp.name, 'features:', comp.features.count, 'bodies:', comp.bRepBodies.count)
    print('timeline items', des.timeline.count, 'niezdrowe:', bad)
    for comp in des.allComponents:
        for sk in comp.sketches:
            sk.isVisible = False
    des.activateRootComponent()
    app.activeViewport.fit()
