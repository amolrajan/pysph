""" This is a setup example that will be used other gas_dynamics problem
    like SodShockTube, BlastWave
"""

import os
import numpy

from pysph.base.utils import get_particle_array as gpa
from pysph.solver.application import Application

class ShockTubeSetup(Application):

    def generate_particles(self, xmin, xmax, dxl, dxr, m, pl, pr, h0,  bx,
            gamma1, ul=0, ur=0, constants={}):
        xt1 = numpy.arange(xmin-bx + 0.5*dxl, 0, dxl)
        xt2 = numpy.arange(0.5*dxr, xmax+bx, dxr )
        xt = numpy.concatenate( [xt1, xt2] )
        leftb_indices = numpy.where( xt <= xmin)[0]
        left_indices =  numpy.where( (xt > xmin) & (xt < 0 ))[0]
        right_indices = numpy.where( (xt >=  0) & (xt < xmax))[0]
        rightb_indices = numpy.where( xt >= xmax)[0]
        x1 = xt[left_indices]
        x2 = xt[right_indices]
        b1 = xt[leftb_indices]
        b2 = xt[rightb_indices]

        x = numpy.concatenate( [x1, x2] )
        b = numpy.concatenate( [b1, b2] )
        right_indices = numpy.where(x>0.0)[0]

        rho = numpy.ones_like(x)*m/dxl
        rho[right_indices] = m/dxr

        p = numpy.ones_like(x)*pl
        p[right_indices] = pr

        u = numpy.ones_like(x)*ul
        u[right_indices] = ur

        h = numpy.ones_like(x) * h0
        m = numpy.ones_like(x)*m
        e = p/(gamma1*rho)
        wij = numpy.ones_like(x)

        bwij = numpy.ones_like(b)
        brho = numpy.ones_like(b)
        bp = numpy.ones_like(b)
        be = bp/(gamma1*brho)
        bm = numpy.ones_like(b)*dxl
        bh = numpy.ones_like(b)*4*h0
        bhtmp = numpy.ones_like(b)
        fluid = gpa(
                constants=constants, name='fluid', x=x, rho=rho, p=p,
                e=e, h=h, m=m, u=u, wij=wij, h0=h.copy()
                )

        boundary = gpa(
                constants=constants, name='boundary', x=b, rho=brho, p=bp,
                e=be, h=bh, m=bm, wij=bwij, h0=bh.copy(), htmp =bhtmp
                )

        self.scheme.setup_properties([fluid, boundary])
        print("1D Shocktube with %d particles"%(fluid.get_number_of_particles()))
        return [fluid, boundary]


    def post_process(self):
        try:
            import matplotlib
            matplotlib.use('Agg')
            from matplotlib import pyplot as plt
        except ImportError:
            print("Post processing requires matplotlib.")
            return
        if self.rank > 0 or len(self.output_files) == 0:
            return

        last_output = self.output_files[-1]
        from pysph.solver.utils import load
        data = load(last_output)
        pa = data['arrays']['fluid']
        x = pa.x
        rho = pa.rho
        e = pa.e
        cs = pa.cs
        u = pa.u
        p = pa.p
        plt.plot(x, rho)
        plt.xlabel('x'); plt.ylabel('rho')
        fig = os.path.join(self.output_dir, "density.png")
        plt.savefig(fig, dpi=300)
        plt.clf()
        plt.plot(x, e)
        plt.xlabel('x'); plt.ylabel('e')
        fig = os.path.join(self.output_dir, "energy.png")
        plt.savefig(fig, dpi=300)
        plt.clf()

        plt.plot(x, rho*u)
        plt.xlabel('x'); plt.ylabel('M')
        fig = os.path.join(self.output_dir, "Machno.png")
        plt.savefig(fig, dpi=300)
        plt.clf()

        plt.plot(x, p)
        plt.xlabel('x'); plt.ylabel('p')
        fig = os.path.join(self.output_dir, "pressure.png")
        plt.savefig(fig, dpi=300)
        plt.clf()

        fname = os.path.join(self.output_dir, 'results.npz')
        numpy.savez(fname, x=x, u=u, e=e, cs=cs, rho=rho, p=p)

    def configure_scheme(self):
        s = self.scheme
        if self.options.scheme == 'mpm':
            s.configure_solver(dt=self.dt, tf=self.tf,
                    adaptive_timestep=True, pfreq=50)
        elif self.options.scheme == 'adke':
            s.configure_solver(dt=self.dt, tf=self.tf,
                    adaptive_timestep=False, pfreq=50)
