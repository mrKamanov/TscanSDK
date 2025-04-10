import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional

def stackImages(imgArray: List[List[np.ndarray]], scale: float, labels: List[List[str]] = []) -> np.ndarray:
    rows = len(imgArray)
    cols = len(imgArray[0])
    rowsAvailable = isinstance(imgArray[0], list)
    width = imgArray[0][0].shape[1]
    height = imgArray[0][0].shape[0]

    def process_image(img: np.ndarray) -> np.ndarray:
        img = cv2.resize(img, (0, 0), None, scale, scale)
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if len(img.shape) == 2 else img

    if rowsAvailable:
        for x in range(rows):
            for y in range(cols):
                imgArray[x][y] = process_image(imgArray[x][y])
        imageBlank = np.zeros((height, width, 3), np.uint8)
        hor = [np.hstack(imgArray[x]) for x in range(rows)]
        ver = np.vstack(hor)
    else:
        imgArray = [process_image(x) for x in imgArray]
        ver = np.hstack(imgArray)

    if labels:
        eachImgWidth = int(ver.shape[1] / cols)
        eachImgHeight = int(ver.shape[0] / rows)
        for d in range(rows):
            for c in range(cols):
                label_width = len(labels[d][c]) * 13 + 27
                cv2.rectangle(ver, 
                            (c * eachImgWidth, eachImgHeight * d),
                            (c * eachImgWidth + label_width, 30 + eachImgHeight * d),
                            (255, 255, 255), 
                            cv2.FILLED)
                cv2.putText(ver, labels[d][c], 
                          (eachImgWidth * c + 10, eachImgHeight * d + 20),
                          cv2.FONT_HERSHEY_COMPLEX, 0.7, (255, 0, 255), 2)
    return ver

def reorder(myPoints: np.ndarray) -> np.ndarray:
    myPoints = myPoints.reshape((4, 2))
    myPointsNew = np.zeros((4, 1, 2), np.int32)
    add = myPoints.sum(1)
    diff = np.diff(myPoints, axis=1)
    myPointsNew[0] = myPoints[np.argmin(add)]
    myPointsNew[3] = myPoints[np.argmax(add)]
    myPointsNew[1] = myPoints[np.argmin(diff)]
    myPointsNew[2] = myPoints[np.argmax(diff)]
    return myPointsNew

def find_contours(img: np.ndarray) -> List[np.ndarray]:
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 1)
    imgCanny = cv2.Canny(imgBlur, 10, 70)
    contours, _ = cv2.findContours(imgCanny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return contours

def rectContour(contours: List[np.ndarray]) -> List[np.ndarray]:
    return sorted(
        [cont for cont in contours 
         if cv2.contourArea(cont) > 50 
         and len(cv2.approxPolyDP(cont, 0.02 * cv2.arcLength(cont, True), True)) == 4],
        key=cv2.contourArea,
        reverse=True
    )

def getCornerPoints(cont: np.ndarray) -> np.ndarray:
    peri = cv2.arcLength(cont, True)
    return cv2.approxPolyDP(cont, 0.02 * peri, True)

def splitBoxes(img: np.ndarray, questions: int, choices: int) -> List[np.ndarray]:
    if img.shape[0] % questions != 0 or img.shape[1] % choices != 0:
        raise ValueError("Изображение не может быть равномерно разделено на указанную сетку.")
    rows = np.vsplit(img, questions)
    return [box for r in rows for box in np.hsplit(r, choices)]

def drawGrid(img: np.ndarray, questions: int = 5, choices: int = 5) -> np.ndarray:
    secW = img.shape[1] // choices
    secH = img.shape[0] // questions
    
    for i in range(questions + 1):
        cv2.line(img, (0, int(secH * i)), (img.shape[1], int(secH * i)), (255, 79, 0), 2)
    
    for i in range(choices + 1):
        cv2.line(img, (int(secW * i), 0), (int(secW * i), img.shape[0]), (255, 79, 0), 2)
    
    return img

def draw_answer_marks(img: np.ndarray, position: Tuple[int, int], is_correct: bool, cell_size: Tuple[int, int]):
    cX, cY = position
    cellW, cellH = cell_size
    mark_size = min(cellW, cellH) // 3
    thickness = max(2, min(cellW, cellH) // 20)
    circle_radius = mark_size + thickness
    
    if is_correct:
        fill_color = (255, 165, 0)
        border_color = (200, 130, 0)
        mark_color = (255, 255, 255)
        
        cv2.circle(img, (cX, cY), circle_radius, fill_color, -1)
        cv2.circle(img, (cX, cY), circle_radius, border_color, thickness)
        
        points = np.array([
            [cX - mark_size, cY],
            [cX - mark_size//2, cY + mark_size//2],
            [cX + mark_size, cY - mark_size//2]
        ])
        
        cv2.polylines(img, [points], isClosed=False, color=(0, 0, 0), thickness=thickness*2)
        cv2.polylines(img, [points], isClosed=False, color=mark_color, thickness=thickness)
        
    else:
        fill_color = (255, 0, 0)
        border_color = (200, 0, 0)
        mark_color = (255, 255, 255)
        
        cv2.circle(img, (cX, cY), circle_radius, fill_color, -1)
        cv2.circle(img, (cX, cY), circle_radius, border_color, thickness)
        
        cv2.line(img, 
                (cX - mark_size//2, cY - mark_size//2),
                (cX + mark_size//2, cY + mark_size//2),
                (0, 0, 0), thickness*2)
        cv2.line(img,
                (cX - mark_size//2, cY + mark_size//2),
                (cX + mark_size//2, cY - mark_size//2),
                (0, 0, 0), thickness*2)
        
        cv2.line(img,
                (cX - mark_size//2, cY - mark_size//2),
                (cX + mark_size//2, cY + mark_size//2),
                mark_color, thickness)
        cv2.line(img,
                (cX - mark_size//2, cY + mark_size//2),
                (cX + mark_size//2, cY - mark_size//2),
                mark_color, thickness)

def showAnswers(img: np.ndarray, myIndex: List[int], grading: List[int], ans: List[int], 
                questions: int = 5, choices: int = 5) -> None:
    secW = img.shape[1] // choices
    secH = img.shape[0] // questions
    cell_size = (secW, secH)
    
    for x in range(questions):
        selected_pos = ((myIndex[x] * secW) + secW // 2, (x * secH) + secH // 2)
        draw_answer_marks(img, selected_pos, grading[x] == 1, cell_size)
        
        if grading[x] == 0:
            correct_pos = ((ans[x] * secW) + secW // 2, (x * secH) + secH // 2)
            mark_size = min(secW, secH) // 4
            cX, cY = correct_pos
            
            cv2.circle(img, correct_pos, mark_size, (0, 200, 0), -1)
            cv2.circle(img, correct_pos, mark_size, (0, 150, 0), 2)
            
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = mark_size / 30
            thickness = max(1, mark_size // 15)
            
            text = "!"
            text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
            text_x = cX - text_size[0] // 2
            text_y = cY + text_size[1] // 2
            
            cv2.putText(img, text, (text_x, text_y), font, font_scale, (0, 0, 0), thickness * 3)
            cv2.putText(img, text, (text_x, text_y), font, font_scale, (255, 255, 255), thickness)

def adjust_image(img: np.ndarray, brightness: float = 0, contrast: float = 1, 
                saturation: float = 1, sharpness: float = 1) -> np.ndarray:
    result = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    avg_a = np.average(result[:, :, 1])
    avg_b = np.average(result[:, :, 2])
    result[:, :, 1] = result[:, :, 1] - ((avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1)
    result[:, :, 2] = result[:, :, 2] - ((avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1)
    img = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)

    img = cv2.convertScaleAbs(img, alpha=contrast, beta=brightness)
    
    b, g, r = cv2.split(img)
    b = cv2.multiply(b, 0.8)
    g = cv2.multiply(g, 1.2)
    r = cv2.multiply(r, 1.2)
    
    img = cv2.merge([b, g, r])
    
    if sharpness != 1:
        blurred = cv2.GaussianBlur(img, (0, 0), 3)
        img = cv2.addWeighted(img, 1 + sharpness, blurred, -sharpness, 0)
    
    return img

def process_video_frame(img: np.ndarray, questions: int, choices: int, correct_answers: List[int], 
                       image_size: int, overlay_mode: bool = False, brightness: float = 0,
                       contrast: float = 1, saturation: float = 1, sharpness: float = 1) -> Tuple:
    try:
        img = adjust_image(img, brightness, contrast, saturation, sharpness)
        new_width = choices * (image_size // choices)
        new_height = questions * (image_size // questions)
        img = cv2.resize(img, (new_width, new_height))
        
        contours = find_contours(img)
        rectCon = rectContour(contours)
        
        if not rectCon:
            raise ValueError("Не удалось найти достаточное количество контуров.")
            
        biggestPoints = getCornerPoints(rectCon[0])
        if biggestPoints.size == 0:
            raise ValueError("Не удалось определить углы контура.")
            
        biggestPoints = reorder(biggestPoints)
        pts1 = np.float32(biggestPoints)
        pts2 = np.float32([[0, 0], [new_width, 0], [0, new_height], [new_width, new_height]])
        
        matrix = cv2.getPerspectiveTransform(pts1, pts2)
        imgWarpColored = cv2.warpPerspective(img, matrix, (new_width, new_height))
        imgWarpGray = cv2.cvtColor(imgWarpColored, cv2.COLOR_BGR2GRAY)
        imgThresh = cv2.threshold(imgWarpGray, 170, 255, cv2.THRESH_BINARY_INV)[1]
        
        boxes = splitBoxes(imgThresh, questions, choices)
        myPixelVal = np.array([[cv2.countNonZero(boxes[i * choices + j]) 
                               for j in range(choices)] for i in range(questions)])
        
        myIndex = np.argmax(myPixelVal, axis=1)
        grading = [1 if correct_answers[i] == myIndex[i] else 0 for i in range(questions)]
        score = (sum(grading) / questions) * 100
        
        incorrect_questions = [
            {
                "question_number": i + 1,
                "selected_answer": myIndex[i] + 1,
                "correct_answer": correct_answers[i] + 1
            }
            for i, grade in enumerate(grading) if grade == 0
        ]
        
        imgFinal = imgWarpColored.copy()
        showAnswers(imgFinal, myIndex, grading, correct_answers, questions, choices)
        drawGrid(imgFinal, questions, choices)
        
        if not overlay_mode:
            return imgFinal, sum(grading), score, incorrect_questions, [int(g) for g in grading]
            
        invMatrix = cv2.getPerspectiveTransform(pts2, pts1)
        imgInvWarp = cv2.warpPerspective(imgFinal, invMatrix, (img.shape[1], img.shape[0]))
        
        mask = np.zeros_like(img, dtype=np.uint8)
        cv2.fillPoly(mask, [np.int32(biggestPoints)], (255, 255, 255))
        
        result = img.copy()
        result = cv2.addWeighted(result, 0.3, imgInvWarp, 0.7, 0)
        
        return result, sum(grading), score, incorrect_questions, [int(g) for g in grading]
        
    except Exception as e:
        print(f"Ошибка обработки кадра: {str(e)}")
        return img, 0, 0, [], []