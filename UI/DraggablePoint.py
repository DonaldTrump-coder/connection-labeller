from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsItem
from PyQt6.QtGui import QColor, QPen
from PyQt6.QtCore import QPointF

class DraggablePoint(QGraphicsEllipseItem):
    def __init__(self, x, y, r, color, canvas):
        super().__init__(x-r, y-r, r*2, r*2)

        self.canvas = canvas
        self.radius = r
        self.edges = []
        
        self.setBrush(color)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        self.old_pos = QPointF(x, y)
    
    def center_pos(self):
        return self.mapToScene(self.rect().center())
    
    def itemChange(self, change, value):
        from UI.canvas import CanvasMode
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            scene_rect = self.scene().sceneRect()
            
            radius = self.rect().width() / 2
            
            new_pos = value

            x = min(max(new_pos.x() + self.old_pos.x(), scene_rect.left()),
                    scene_rect.right())
            y = min(max(new_pos.y() + self.old_pos.y(), scene_rect.top()),
                    scene_rect.bottom())

            corrected_pos = QPointF(x - self.old_pos.x(), y - self.old_pos.y())

            return corrected_pos
        
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionHasChanged:
            if self.canvas.mode == CanvasMode.Move:
                new_pos = self.center_pos()
                dx = new_pos.x() - self.polygon.center_x
                dy = new_pos.y() - self.polygon.center_y
                self.polygon.dx = dx
                self.polygon.dy = dy
                
                self.canvas.add_ghost(self.old_pos)
                for e in self.edges:
                    e.update_position()
        return super().itemChange(change, value)
    
class Edge(QGraphicsLineItem):
    def __init__(self, p1, p2):
        super().__init__()
        self.p1 = p1
        self.p2 = p2

        self.setPen(QPen(QColor("green"), 2))

        p1.edges.append(self)
        p2.edges.append(self)

        self.update_position()

    def update_position(self):
        p1 = self.p1.center_pos()
        p2 = self.p2.center_pos()
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())