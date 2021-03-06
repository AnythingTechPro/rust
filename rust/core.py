import os
import pygame
import pygame.locals
from PIL import Image
from rust import objects, task

class CoreDisplay(objects.GameObject):

    def __init__(self, engine, width, height, flags=pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.RESIZABLE, depth=0):
        super(CoreDisplay, self).__init__()

        self.engine = engine
        self.color = pygame.Color(0, 0, 0)
        self.surface = pygame.display.set_mode([width, height], flags, depth)

    def fill(self, color=None):
        self.surface.fill(color)

    def flip(self):
        pygame.display.flip()

    def update(self):
        self.fill(self.color)

    def destroy(self):
        pygame.display.quit()

class CoreLoaderError(IOError):
    """
    A core loader specific io error
    """

class CoreLoader(object):

    def __init__(self, engine):
        self.engine = engine

    def load_image(self, filename, is_transparent=False, flipped=False):
        if not os.path.exists(filename):
            raise CoreLoaderError('Failed to load image %s!' % filename)

        image = Image.open(filename)
        image = pygame.image.fromstring(image.tobytes(), image.size, image.mode, flipped)

        if is_transparent:
            image = image.convert_alpha()

        return self.engine.renderer.game_object_manager.create(image)

    def load_transparent_image(self, filename, flipped=False):
        return self.load_image(filename, True, flipped)

    def load_audio(self, filename, is_music=False):
        pass

    def load_object(self, class_object):
        return self.engine.renderer.game_object_manager.create_with(class_object, None)

    def load_scene(self, *args, **kwargs):
        return self.engine.renderer.game_object_manager.create_scene(*args, **kwargs)

    def destroy(self):
        pass

class CoreRendererError(RuntimeError):
    """
    A core render specific runtime error
    """

class CoreRenderer(object):

    def __init__(self, engine):
        self.engine = engine
        self.game_object_manager = objects.GameObjectManager(engine)

    def setup(self):
        self.game_object_manager.setup()

    def update(self):
        if self.game_object_manager.active_scene:
            self.game_object_manager.active_scene.update()

        for game_object in self.game_object_manager.get_game_objects():
            if not game_object.parent or game_object.surface.get_locked():
                continue

            game_object.parent.blit(game_object.surface, game_object.rect)

        self.engine.display.flip()

    def render(self, surface, parent=None):
        if surface.parent:
            raise CoreRendererError('Cannot render an object that\'s already rendered!')

        if not parent:
            parent = self.engine.display.surface

        surface.parent = parent

    def render_scene(self, scene_object):
        self.game_object_manager.active_scene = scene_object

    def destroy(self):
        self.game_object_manager.destroy()

class CoreEngine(object):

    def __init__(self, height=800, width=600):
        self.display = CoreDisplay(self, height, width)
        self.loader = CoreLoader(self)
        self.renderer = CoreRenderer(self)
        self.task_manager = task.TaskManager()
        self.shutdown = False

    def setup(self):
        self.renderer.setup()

    def update(self):
        self.display.update()
        self.renderer.update()

    def destroy(self):
        self.display.destroy()
        self.renderer.destroy()

    def mainloop(self):
        while not self.shutdown:
            for event in pygame.event.get():
                if event.type == pygame.locals.QUIT:
                    return

            self.update()

    def run(self):
        self.task_manager.run()

        try:
            self.mainloop()
        except (KeyboardInterrupt, SystemExit):
            self.quit()

        self.destroy()

    def quit(self):
        self.shutdown = True
