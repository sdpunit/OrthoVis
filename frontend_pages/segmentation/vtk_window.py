# VTK imports
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtkmodules.all as vtk


class VTKWidget(QVTKRenderWindowInteractor):
    def __init__(self, parent=None):
        super().__init__(parent)

       
        # Get the VTK render window
        render_window = self.GetRenderWindow()

        # Create a VTK renderer and add it to the render window
        renderer = vtk.vtkRenderer()
        render_window.AddRenderer(renderer)

        # Create some VTK actor (e.g., a sphere)
        sphere_source = vtk.vtkSphereSource()
        sphere_source.SetRadius(1.0)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(sphere_source.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        renderer.AddActor(actor)

        # Set background color
        renderer.SetBackground(0.2, 0.3, 0.4)

        # # Initialize and start the interactor
        self.Initialize()
        self.Start()

        # # Optional: render once
        # render_window.Render()