from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsEllipseItem, QGraphicsPixmapItem
from PyQt6.QtGui import QPen, QColor, QImage, QPixmap, QPainter
from PyQt6.QtCore import Qt
from enum import Enum, auto
import base64
import numpy as np
import cv2
from dataclasses import dataclass
import random
from UI.DraggablePoint import DraggablePoint, Edge
import math

"""
json:
{
    "version": ,
    "flags": ,
    "shapes": [
        {},
        {},
        ...
    ],
    "imagePath": ,
    "imageData": ,
    "imageWidth": ,
    "imageWidth": ,
    (added)
    "connections": [[1, 2], [1, 3], ...]  (start from 1)
}
shapes:
{
    "label": ,
    "points": [
        [x1, y1],
        [x2, y2],
        ...
    ],
    "group_id": ,
    "description": ,
    "shape_type": ,
    "flags": ,
    "mask": ,
(added)
    "dx": ,
    "dy": 
}
"""

class CanvasMode(Enum):
    Display = auto()
    Move = auto()
    Connect = auto()
    Delete = auto()
    
@dataclass
class Polygon:
    label: str
    points: np.ndarray
    center_x: float
    center_y: float
    dx: float = 0
    dy: float = 0

class Canvas(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        self.mode = CanvasMode.Display
        
        self.polygons = []
        self.edges = []
        self.points = []
        
        self.selected_point = None
        self.temp_line = None
        self.start_point = None
        
    def set_mode(self, mode):
        self.mode = mode

        movable = (mode == CanvasMode.Move)
        for p in self.points:
            p.setFlag(p.GraphicsItemFlag.ItemIsMovable, movable)

        self.selected_point = None
        
    def show_image(self, image):
        h, w, ch = image.shape
        bytes_per_line = ch * w
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        qimg = QImage(
            rgb_image.data, w, h,
            bytes_per_line,
            QImage.Format.Format_RGB888
        )
        pixmap = QPixmap.fromImage(qimg)
        self.image_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.image_item)
        
    def get_image_scene_rect(self):
        return self.image_item.mapToScene(
            self.image_item.boundingRect()
        ).boundingRect()
        
    def draw_polygons(self):
        for polygon in self.polygons:
            pts = polygon.points
            
            color = QColor(
                random.randint(50, 255),
                random.randint(50, 255),
                random.randint(50, 255)
            )
            pen = QPen(color, 2)
            
            for i in range(len(pts)):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % len(pts)]
                self.scene.addLine(x1, y1, x2, y2, pen)
            p = DraggablePoint(polygon.center_x, polygon.center_y, 4, color, self)
            p.polygon = polygon
            self.scene.addItem(p)
            self.points.append(p)
            
    def add_ghost(self, pos):
        from PyQt6.QtWidgets import QGraphicsEllipseItem

        ghost = QGraphicsEllipseItem(pos.x()-3, pos.y()-3, 6, 6)
        ghost.setBrush(QColor(200,200,200,120))
        self.scene.addItem(ghost)
        
    def load_json(self, json_data):
        image = None
        self.json_data = json_data
        
        # load image
        if json_data.get("imageData"):
            img_data = base64.b64decode(json_data["imageData"])
            np_arr = np.frombuffer(img_data, np.uint8)
            image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            self.show_image(image=image)
        
        # load polygons
        self.polygons = []
        for shape in json_data['shapes']:
            if shape['shape_type'] == 'polygon':
                points = np.array(shape['points'], dtype=float) # points list
                label = shape['label']
                xmin = np.min(points[:, 0])
                xmax = np.max(points[:, 0])
                ymin = np.min(points[:, 1])
                ymax = np.max(points[:, 1])
                center_x = (xmin + xmax) / 2
                center_y = (ymin + ymax) / 2
                self.polygons.append(Polygon(label=label,
                                             points=points,
                                             center_x=center_x,
                                             center_y=center_y
                                             )
                                     )
        self.draw_polygons()
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        
    def find_nearest_point(self, pos, threshold=10):
        for p in self.points:
            p_pos = p.center_pos()
            dist = (p_pos - pos).manhattanLength()
            if dist < threshold:
                return p
        return None
    
    def point_to_segment_distance(self, p, a, b):
        px, py = p.x(), p.y()
        x1, y1 = a.x(), a.y()
        x2, y2 = b.x(), b.y()

        dx = x2 - x1
        dy = y2 - y1

        if dx == 0 and dy == 0:
            return math.hypot(px - x1, py - y1)

        t = ((px - x1)*dx + (py - y1)*dy) / (dx*dx + dy*dy)
        t = max(0, min(1, t))

        proj_x = x1 + t*dx
        proj_y = y1 + t*dy

        return math.hypot(px - proj_x, py - proj_y)
    
    def find_nearest_edge(self, pos, threshold=10):
        nearest = None
        min_dist = float("inf")

        for e in self.edges:
            p1 = e.p1.center_pos()
            p2 = e.p2.center_pos()

            dist = self.point_to_segment_distance(pos, p1, p2)

            if dist < threshold and dist < min_dist:
                nearest = e
                min_dist = dist

        return nearest
    
    def remove_edge(self, edge):
        if edge in edge.p1.edges:
            edge.p1.edges.remove(edge)
        if edge in edge.p2.edges:
            edge.p2.edges.remove(edge)

        if edge in self.edges:
            self.edges.remove(edge)

        self.scene.removeItem(edge)
    
    def mousePressEvent(self, event):
        if self.mode == CanvasMode.Connect:
            pos = self.mapToScene(event.pos())

            p = self.find_nearest_point(pos)
            if p:
                self.start_point = p

                from PyQt6.QtWidgets import QGraphicsLineItem
                self.temp_line = QGraphicsLineItem()
                self.temp_line.setPen(QPen(QColor("green"), 2, Qt.PenStyle.DashLine))

                self.scene.addItem(self.temp_line)

            return
        
        if self.mode == CanvasMode.Delete:
            pos = self.mapToScene(event.pos())
            edge = self.find_nearest_edge(pos, threshold=5)

            if edge:
                self.remove_edge(edge)

            return

        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if self.mode == CanvasMode.Connect and self.temp_line and self.start_point:
            pos = self.mapToScene(event.pos())

            p1 = self.start_point.center_pos()

            self.temp_line.setLine(
                p1.x(), p1.y(),
                pos.x(), pos.y()
            )
            return

        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        if self.mode == CanvasMode.Connect and self.start_point:
            pos = self.mapToScene(event.pos())

            end_point = self.find_nearest_point(pos)

            if self.temp_line:
                self.scene.removeItem(self.temp_line)
                self.temp_line = None

            if end_point and end_point != self.start_point:
                edge = Edge(self.start_point, end_point)
                self.scene.addItem(edge)
                self.edges.append(edge)

            self.start_point = None
            return

        super().mouseReleaseEvent(event)
        
    def save(self):
        for idx, shape in enumerate(self.json_data["shapes"]):
            shape["dx"] = self.polygons[idx].dx
            shape["dy"] = self.polygons[idx].dy
        connections = []
        for e in self.edges:
            i = self.points.index(e.p1)
            j = self.points.index(e.p2)
            connections.append([i + 1, j + 1])
        self.json_data["connections"] = connections
        return self.json_data