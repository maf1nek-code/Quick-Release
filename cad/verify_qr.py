"""Weryfikacja geometrii zespolu QR w aktywnym dokumencie Fusion (tylko odczyt)."""
import adsk.core, adsk.fusion, math


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    tmp = adsk.fusion.TemporaryBRepManager.get()
    bodies = {}
    for occ in root.occurrences:
        c = occ.component
        print('%-24s bodies=%d' % (c.name, c.bRepBodies.count))
        b = c.bRepBodies.item(0)
        bodies[c.name[0]] = b
        pp = b.physicalProperties
        print('   solid=%s faces=%d shells=%d lumps=%d vol=%.1f cm3 area=%.0f mm2' % (
            b.isSolid, b.faces.count, b.shells.count, b.lumps.count, b.volume, b.area * 100))
    A, B, C = bodies['A'], bodies['B'], bodies['C']

    last = {}

    def inter(b1, b2, m2=None):
        t1 = tmp.copy(b1)
        t2 = tmp.copy(b2)
        if m2:
            tmp.transform(t2, m2)
        tmp.booleanOperation(t1, t2, adsk.fusion.BooleanTypes.IntersectionBooleanType)
        if not t1.faces.count:
            last['bb'] = None
            return 0.0
        bb = t1.boundingBox
        last['bb'] = '[x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f]' % (bb.minPoint.x * 10, bb.maxPoint.x * 10, bb.minPoint.y * 10, bb.maxPoint.y * 10, bb.minPoint.z * 10, bb.maxPoint.z * 10)
        return t1.volume * 1000

    def T(dx=0, dy=0, dz=0):
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(dx / 10, dy / 10, dz / 10)
        return m

    def Rz(deg):
        m = adsk.core.Matrix3D.create()
        m.setToRotation(math.radians(deg), adsk.core.Vector3D.create(0, 0, 1), adsk.core.Point3D.create(0, 0, 0))
        return m

    up = {p.name: p.value for p in des.userParameters}
    lock_z = up['qr_lock_z']

    def Ry_axis(deg):
        m = adsk.core.Matrix3D.create()
        m.setToRotation(math.radians(deg), adsk.core.Vector3D.create(0, 1, 0), adsk.core.Point3D.create(0, 0, lock_z))
        return m

    print('--- kolizje w pozycji nominalnej [mm3]')
    print('A-B', round(inter(A, B), 3), last['bb'])
    print('A-C', round(inter(A, C), 3), ' B-C', round(inter(B, C), 3))
    print('--- faza gwintu: obrot sruby wokol osi -> kolizja z B / z A')
    best = None
    for a in range(0, 360, 5):
        vb = inter(B, C, Ry_axis(a)); bbx = last['bb']
        va = inter(A, C, Ry_axis(a))
        if best is None or vb + va < best[1]:
            best = (a, vb + va)
        if vb < 3.0:
            print('  %3d deg: B %.3f  A %.3f %s' % (a, vb, va, bbx))
    print('najlepszy kat', best)
    print('--- dosuwanie B w kierunku -Y (klin): kolizja A-B')
    for s in (0.0, -0.2, -0.4, -0.6, -1.0, -2.0):
        print('  dy=%5.1f : %.3f' % (s, inter(A, B, T(dy=s))))
    print('--- wysuwanie B w kierunku +Y (bez sruby): kolizja A-B')
    for s in range(0, 31, 3):
        print('  dy=%3d : %.3f' % (s, inter(A, B, T(dy=s))))
    print('--- podnoszenie B w osi Z przy roznych wysunieciach')
    for s in (0, 4, 8, 12, 14, 15, 16, 18):
        vals = [inter(A, B, T(dy=s, dz=z)) for z in (0.5, 2, 5, 9)]
        print('  dy=%2d : dz 0.5/2/5/9 -> %s' % (s, ' '.join('%.2f' % x for x in vals)))
    print('--- blokada ksztaltowa w pozycji nominalnej')
    print('  obrot +0.5 deg wokol Z:', round(inter(A, B, Rz(0.5)), 3), '  -0.5 deg:', round(inter(A, B, Rz(-0.5)), 3))
    print('  przesuw X +0.3:', round(inter(A, B, T(dx=0.3)), 3), '  X -0.3:', round(inter(A, B, T(dx=-0.3)), 3))
    print('--- sruba: wykrecanie (ruch -Y) kolizja z B (przy najlepszej fazie pomijamy obrot -> tylko zasieg)')
    for s in (0, -6, -9, -9.5, -10, -12):
        t = tmp.copy(C)
        tmp.transform(t, T(dy=s))
        bb = t.boundingBox
        print('  dy=%5.1f : czubek sruby y=%.2f' % (s, bb.maxPoint.y * 10))
    bbB = None
    for f in B.faces:
        g = f.geometry
        if g.objectType == adsk.core.Plane.classType() and abs(abs(g.normal.y) - 1) < 1e-6 and abs(g.origin.y * 10 - up['qr_y_tip'] * 10) < 1e-3:
            bbB = f.boundingBox
    print('czolo piora B (y_tip):', None if bbB is None else '[x %.2f..%.2f, z %.2f..%.2f]' % (bbB.minPoint.x * 10, bbB.maxPoint.x * 10, bbB.minPoint.z * 10, bbB.maxPoint.z * 10))
