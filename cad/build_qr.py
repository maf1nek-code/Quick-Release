"""FFBeast sliding-wedge Quick Release - model generator for Fusion 360.

How to run: Fusion 360 -> Utilities -> Scripts and Add-Ins -> (add this file) -> Run,
or through a Fusion MCP server (featureType="script").
Change the values in the P dictionary and run it again - the script rebuilds the whole
assembly from scratch in a new document.  All dimensions in mm / degrees.

Coordinate system:
  Z = wheel axis, Z=0 = flange face (wheel side), +Z towards the driver
  Y = slide-in direction; the wheel (part B) slides in along -Y, towards the lock tower
"""
import adsk.core, adsk.fusion, math

P = {
    # --- interface with the flange / wheel (measured from the STL files) ---
    'qr_dia':        (86.0, 'mm', 'Outer diameter of parts A and B'),
    'pcd':           (70.0, 'mm', 'Pitch circle of the 6 holes (measured from the STL: 70.00)'),
    'a_hole_d':      (5.5,  'mm', 'M5 clearance hole in part A'),
    'a_cbore_d':     (10.4, 'mm', 'Counterbore for an M5 ISO 7380 head (head 9.5 mm)'),
    'a_under_head':  (4.8,  'mm', 'Material under the screw heads in part A'),
    'b_hole_d':      (5.4,  'mm', 'M5 clearance hole in part B'),
    'b_nut_af':      (8.3,  'mm', 'M5 nut pocket (8.0 across flats + clearance)'),
    'b_nut_depth':   (6.0,  'mm', 'Nut pocket depth from the contact plane'),
    # --- wedge geometry ---
    'a_floor':       (8.0,  'mm', 'Channel floor thickness in part A'),
    'dv_h':          (8.0,  'mm', 'Dovetail height'),
    'b_plate':       (10.0, 'mm', 'Plate thickness of part B'),
    'alpha':         (14.0, 'deg', 'Half-angle of the V wedge in plan view'),
    'beta':          (35.0, 'deg', 'Dovetail undercut from vertical'),
    'wf_tip':        (14.0, 'mm', 'Channel half-width at the floor, at the tongue tip'),
    'y_tip':         (-22.0, 'mm', 'Tongue tip position (nominal seated position)'),
    'y_wall':        (-25.0, 'mm', 'Channel end wall (3 mm gap = reserve for wear)'),
    'y_tail':        (24.5, 'mm', 'Rear end of the tongue'),
    'fit_clr':       (0.10, 'mm', 'Tongue side clearance per side (X) - fit calibration'),
    'floor_gap':     (0.30, 'mm', 'Gap between tongue and channel floor'),
    'r_floor':       (0.8,  'mm', 'Fillet at the root of the part A lip'),
    'c_lip':         (1.7,  'mm', 'Chamfer on the part A lip edge'),
    'r_root':        (0.8,  'mm', 'Fillet at the root of the part B tongue'),
    'c_tongue':      (1.2,  'mm', 'Chamfer on the lower tongue edges'),
    # --- lock ---
    'lock_z':        (17.0, 'mm', 'Height of the locking screw axis'),
    'tower_hw':      (9.0,  'mm', 'Half-width of the lock tower'),
    'tower_top':     (25.0, 'mm', 'Top face of the tower'),
    'y_flat':        (-42.0, 'mm', 'Flat stop face for the knob'),
    'notch_clr':     (0.7,  'mm', 'Clearance of the part B notch around the tower'),
    'thr_pilot':     (9.0,  'mm', 'Tap hole for the internal Tr12x3 thread'),
    'thr_depth':     (18.0, 'mm', 'Depth of the threaded hole in the tongue'),
    'cap_len':       (5.0,  'mm', 'Length of the thread that keeps the screw from falling out'),
    'lock_clr_d':    (11.8, 'mm', 'Screw clearance hole in the tower'),
    'scr_thr_d':     (11.0, 'mm', 'Screw thread diameter (Tr11x3 - deliberately smaller than Tr12)'),
    'scr_thr_len':   (12.0, 'mm', 'Screw thread length'),
    'scr_neck_d':    (8.2,  'mm', 'Screw neck'),
    'scr_pilot_d':   (7.4,  'mm', 'Pilot at the screw tip'),
    'scr_pilot_len': (2.0,  'mm', 'Pilot length'),
    'scr_collar_d':  (16.4, 'mm', 'Screw stop collar'),
    'scr_collar_t':  (2.5,  'mm', 'Collar thickness'),
    'scr_wing_w':    (15.0, 'mm', 'Wing width'),
    'scr_wing_t':    (7.0,  'mm', 'Wing thickness'),
    'scr_wing_len':  (14.0, 'mm', 'Wing length'),
}
THREAD_TYPE = 'ISO Metric Trapezoidal Threads'
THREAD_INT = ('TR12x3', '7H')
THREAD_EXT = ('TR11x3', '7e')

VI = adsk.core.ValueInput
OP = adsk.fusion.FeatureOperations


def v(k):
    return P[k][0]


def wf(y):
    """channel half-width at the floor (z = a_floor) as a function of y"""
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
    """pts: list of (x, y, z) in mm, model coordinates"""
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
        # limit the operation to this component's body (otherwise a cut also hits the other parts)
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
    """straight edges at height z that run mostly along Y"""
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
    assert edges.count > 0, 'no edges for ' + name
    ff = comp.features.filletFeatures
    fi = ff.createInput()
    fi.edgeSetInputs.addConstantRadiusEdgeSet(edges, VI.createByString('%.4f mm' % r_mm), True)
    f = ff.add(fi)
    f.name = name
    return f


def chamfer(comp, edges, d_mm, name):
    assert edges.count > 0, 'no edges for ' + name
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
    raise RuntimeError('cylindrical face r=%s not found' % r_mm)


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
    c.name = 'A_base_QR'
    R = v('qr_dia') / 2.0
    zt = v('a_floor') + v('dv_h')          # contact plane
    tb = math.tan(math.radians(v('beta')))

    sk = new_sketch(c, c.xYConstructionPlane, 'A_outline')
    circle(sk, (0, 0, 0), 2 * R)
    extrude(c, sk.profiles.item(0), zt, OP.NewBodyFeatureOperation, 'A_disc')
    body = c.bRepBodies.item(0)
    body.name = 'A_base_QR'

    # undercut V channel: loft between a section at the floor and one above the contact plane
    yb, ye, ov = v('y_wall'), R + 8.0, 0.5
    s1 = new_sketch(c, plane_z(c, v('a_floor'), 'A_pl_floor'), 'A_channel_floor')
    poly(s1, [(-wf(yb), yb, v('a_floor')), (wf(yb), yb, v('a_floor')), (wf(ye), ye, v('a_floor')), (-wf(ye), ye, v('a_floor'))])
    d = (v('dv_h') + ov) * tb
    s2 = new_sketch(c, plane_z(c, zt + ov, 'A_pl_top'), 'A_channel_top')
    poly(s2, [(-wf(yb) + d, yb, zt + ov), (wf(yb) - d, yb, zt + ov), (wf(ye) - d, ye, zt + ov), (-wf(ye) + d, ye, zt + ov)])
    loft(c, s1.profiles.item(0), s2.profiles.item(0), OP.CutFeatureOperation, 'A_V_channel')
    print('A after channel', bbox(body))

    fillet(c, line_edges(body, v('a_floor')), v('r_floor'), 'A_lip_root_fillet')
    chamfer(c, line_edges(body, zt), v('c_lip'), 'A_lip_chamfer')

    # lock tower
    s = new_sketch(c, plane_z(c, zt, 'A_pl_contact'), 'A_tower')
    hw = v('tower_hw')
    poly(s, [(-hw, -R - 3, zt), (hw, -R - 3, zt), (hw, v('y_wall'), zt), (-hw, v('y_wall'), zt)])
    extrude(c, s.profiles.item(0), v('tower_top') - zt, OP.JoinFeatureOperation, 'A_tower')
    s = new_sketch(c, c.xYConstructionPlane, 'A_flat')
    poly(s, [(-hw - 6, -R - 6, 0), (hw + 6, -R - 6, 0), (hw + 6, v('y_flat'), 0), (-hw - 6, v('y_flat'), 0)])
    extrude(c, s.profiles.item(0), v('tower_top') + 5, OP.CutFeatureOperation, 'A_stop_face')
    print('A after tower', bbox(body))

    # 6 mounting holes + counterbores
    s = new_sketch(c, c.xYConstructionPlane, 'A_M5_holes')
    for (x, y) in hole_positions():
        circle(s, (x, y, 0), v('a_hole_d'))
    extrude(c, all_profiles(s), v('tower_top') + 5, OP.CutFeatureOperation, 'A_M5_holes')
    zu = v('a_under_head')
    s = new_sketch(c, plane_z(c, zu, 'A_pl_under_head'), 'A_counterbores')
    for (x, y) in hole_positions():
        circle(s, (x, y, zu), v('a_cbore_d'))
    extrude(c, all_profiles(s), v('tower_top') + 5, OP.CutFeatureOperation, 'A_counterbores')

    # locking screw hole: retaining thread + clearance hole
    pl, sg = plane_y(c, v('y_flat'), 'A_pl_stop')
    s = new_sketch(c, pl, 'A_thread_hole')
    circle(s, (0, v('y_flat'), v('lock_z')), v('thr_pilot'))
    extrude(c, s.profiles.item(0), sg * (v('y_wall') - v('y_flat') + 1.0), OP.CutFeatureOperation, 'A_tap_hole')
    y0 = v('y_flat') + v('cap_len')
    pl, sg = plane_y(c, y0, 'A_pl_clearance')
    s = new_sketch(c, pl, 'A_clearance_hole')
    circle(s, (0, y0, v('lock_z')), v('lock_clr_d'))
    extrude(c, s.profiles.item(0), sg * (v('y_wall') - y0 + 1.0), OP.CutFeatureOperation, 'A_screw_clearance_hole')
    f = cyl_face(body, v('thr_pilot') / 2.0, lambda f: f.boundingBox.maxPoint.y * 10 < y0 + 0.01)
    thread(c, f, True, 'A_retaining_thread_Tr12x3')

    chamfer(c, rim_edges(body, 0.0, R), 0.6, 'A_bottom_chamfer')
    chamfer(c, rim_edges(body, zt, R), 0.8, 'A_top_chamfer')
    print('A done', bbox(body))
    return occ


def build_B(root):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    c = occ.component
    c.name = 'B_wheel_adapter'
    R = v('qr_dia') / 2.0
    zt = v('a_floor') + v('dv_h')
    zb = v('a_floor') + v('floor_gap')
    ztop = zt + v('b_plate')
    tb = math.tan(math.radians(v('beta')))
    cx = v('fit_clr')

    s = new_sketch(c, plane_z(c, zt, 'B_pl_contact'), 'B_outline')
    circle(s, (0, 0, zt), 2 * R)
    extrude(c, s.profiles.item(0), v('b_plate'), OP.NewBodyFeatureOperation, 'B_plate')
    body = c.bRepBodies.item(0)
    body.name = 'B_wheel_adapter'

    # V tongue (loft from the tongue underside into the plate)
    y1, y2, ov = v('y_tip'), v('y_tail'), 0.5
    def hwz(y, z):
        return wf(y) - (z - v('a_floor')) * tb - cx
    s1 = new_sketch(c, plane_z(c, zb, 'B_pl_tongue_bottom'), 'B_tongue_bottom')
    poly(s1, [(-hwz(y1, zb), y1, zb), (hwz(y1, zb), y1, zb), (hwz(y2, zb), y2, zb), (-hwz(y2, zb), y2, zb)])
    s2 = new_sketch(c, plane_z(c, zt + ov, 'B_pl_root'), 'B_tongue_root')
    poly(s2, [(-hwz(y1, zt + ov), y1, zt + ov), (hwz(y1, zt + ov), y1, zt + ov), (hwz(y2, zt + ov), y2, zt + ov), (-hwz(y2, zt + ov), y2, zt + ov)])
    loft(c, s1.profiles.item(0), s2.profiles.item(0), OP.JoinFeatureOperation, 'B_V_tongue')
    print('B after tongue', bbox(body))

    chamfer(c, line_edges(body, zb), v('c_tongue'), 'B_tongue_bottom_chamfer')
    fillet(c, line_edges(body, zt), v('r_root'), 'B_tongue_root_fillet')

    # notch for the tower
    hw = v('tower_hw') + v('notch_clr')
    s = new_sketch(c, plane_z(c, zt, 'B_pl_contact2'), 'B_notch')
    poly(s, [(-hw, -R - 5, zt), (hw, -R - 5, zt), (hw, y1, zt), (-hw, y1, zt)])
    extrude(c, s.profiles.item(0), v('b_plate') + 2, OP.CutFeatureOperation, 'B_tower_notch')

    # wheel holes + nut pockets
    s = new_sketch(c, plane_z(c, zb - 1.0, 'B_pl_holes'), 'B_M5_holes')
    for (x, y) in hole_positions():
        circle(s, (x, y, zb - 1.0), v('b_hole_d'))
    extrude(c, all_profiles(s), ztop - zb + 3.0, OP.CutFeatureOperation, 'B_M5_holes')
    s = new_sketch(c, plane_z(c, zt, 'B_pl_contact3'), 'B_pockets')
    rc = v('b_nut_af') / 2.0 / math.cos(math.radians(30))
    for (x, y) in hole_positions():
        poly(s, [(x + rc * math.cos(math.radians(a)), y + rc * math.sin(math.radians(a)), zt) for a in range(0, 360, 60)])
    profs = adsk.core.ObjectCollection.create()
    for p in s.profiles:
        profs.add(p)
    extrude(c, profs, v('b_nut_depth'), OP.CutFeatureOperation, 'B_M5_nut_pockets')

    # threaded hole for the locking screw
    pl, sg = plane_y(c, y1, 'B_pl_front')
    s = new_sketch(c, pl, 'B_thread_hole')
    circle(s, (0, y1, v('lock_z')), v('thr_pilot'))
    extrude(c, s.profiles.item(0), sg * v('thr_depth'), OP.CutFeatureOperation, 'B_tap_hole')
    f = cyl_face(body, v('thr_pilot') / 2.0, lambda f: True)
    thread(c, f, True, 'B_lock_thread_Tr12x3')

    chamfer(c, rim_edges(body, ztop, R), 0.6, 'B_top_chamfer')
    chamfer(c, rim_edges(body, zt, R), 0.8, 'B_bottom_chamfer')
    print('B done', bbox(body))
    return occ


def build_C(root):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    c = occ.component
    c.name = 'C_locking_screw'
    z0 = v('lock_z')
    y_sh = v('y_wall')                       # end of the neck / start of the thread (tightened)
    y_fl = v('y_flat')

    pl, sg = plane_y(c, y_sh, 'C_pl_thread')
    s = new_sketch(c, pl, 'C_thread')
    circle(s, (0, y_sh, z0), v('scr_thr_d'))
    extrude(c, s.profiles.item(0), sg * v('scr_thr_len'), OP.NewBodyFeatureOperation, 'C_thread_shank')
    body = c.bRepBodies.item(0)
    body.name = 'C_locking_screw'
    f = cyl_face(body, v('scr_thr_d') / 2.0, lambda f: True)
    thread(c, f, False, 'C_thread_Tr11x3')
    # pilot at the tip (smaller than the nut's minor diameter) - helps find the thread
    yt = y_sh + v('scr_thr_len')
    plt, sgt = plane_y(c, yt, 'C_pl_tip')
    s = new_sketch(c, plt, 'C_pilot')
    circle(s, (0, yt, z0), v('scr_pilot_d'))
    extrude(c, s.profiles.item(0), sgt * v('scr_pilot_len'), OP.JoinFeatureOperation, 'C_pilot')

    s = new_sketch(c, pl, 'C_neck')
    circle(s, (0, y_sh, z0), v('scr_neck_d'))
    extrude(c, s.profiles.item(0), -sg * (y_sh - y_fl), OP.JoinFeatureOperation, 'C_neck')

    pl2, sg2 = plane_y(c, y_fl, 'C_pl_collar')
    s = new_sketch(c, pl2, 'C_collar')
    circle(s, (0, y_fl, z0), v('scr_collar_d'))
    extrude(c, s.profiles.item(0), -sg2 * v('scr_collar_t'), OP.JoinFeatureOperation, 'C_collar')

    yw = y_fl - v('scr_collar_t')
    pl3, sg3 = plane_y(c, yw, 'C_pl_wing')
    s = new_sketch(c, pl3, 'C_wing')
    w, t = v('scr_wing_w') / 2.0, v('scr_wing_t') / 2.0
    poly(s, [(-w, yw, z0 - t), (w, yw, z0 - t), (w, yw, z0 + t), (-w, yw, z0 - t + 2 * t)])
    extrude(c, s.profiles.item(0), -sg3 * v('scr_wing_len'), OP.JoinFeatureOperation, 'C_wing')

    # flat face for printing lying down (underside of the wing = print bed)
    yc = yw - v('scr_wing_len') - 2.0
    pl4, sg4 = plane_y(c, yc, 'C_pl_cut')
    s = new_sketch(c, pl4, 'C_print_flat')
    poly(s, [(-15, yc, z0 - 15), (15, yc, z0 - 15), (15, yc, z0 - t), (-15, yc, z0 - t)])
    extrude(c, s.profiles.item(0), sg4 * 60.0, OP.CutFeatureOperation, 'C_print_flat')
    print('C done', bbox(body))
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
            raise RuntimeError('parameter %s: %s' % (k, e))
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
    print('timeline items', des.timeline.count, 'unhealthy:', bad)
    for comp in des.allComponents:
        for sk in comp.sketches:
            sk.isVisible = False
    des.activateRootComponent()
    app.activeViewport.fit()
