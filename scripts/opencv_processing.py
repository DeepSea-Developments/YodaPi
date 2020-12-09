import cv2
import numpy as np
import numpy.ma as ma


class OpenCVProcessor:
    """This class is in charge of all the OpenCV Processing"""

    REF_TEMP = 33.2
    CAM_SENSITIVITY = 26

    THRESHOLD_HUMAN_TEMP = 32

    TEMP_FLOOR = 22
    TEMP_CEIL = 40

    REF_HEIGHT = 20

    REF_MEASURE_HEIGHT = 10
    REF_MEASURE_WEIGHT = 30
    REF_TOPLEFT_X = 45
    REF_TOPLEFT_Y = 69

    x1_ref = REF_TOPLEFT_X
    x2_ref = REF_TOPLEFT_X + REF_MEASURE_WEIGHT
    y1_ref = REF_TOPLEFT_Y
    y2_ref = REF_TOPLEFT_Y + REF_MEASURE_HEIGHT

    THRESHOLD_AREA_MIN = 100
    THRESHOLD_AREA_MAX = 100000

    OUTPUT_IMAGE_SCALE = 5

    A = 91.3
    B = -3.67
    C = 0.0608

    calibrating = False

    def __init__(self, calibrating=False):
        self.calibrating = calibrating

    def calculate_temp_human(self, temp):
        return self.A + self.B * temp + self.C * temp * temp

    @staticmethod
    def scale_contour(cnt, scale):
        cnt_scaled = cnt * scale
        cnt_scaled = cnt_scaled.astype(np.int32)

        return cnt_scaled

    def process_frame(self, frame_raw):
        frame_raw = cv2.flip(frame_raw, 1)
        normalized = frame_raw / self.CAM_SENSITIVITY
        # mean_t_ref = np.median(normalized[80 - self.REF_MEASURE_HEIGHT:80, 0:80])
        _mean_t_ref = np.median(normalized[self.y1_ref: self.y2_ref, self.x1_ref: self.x2_ref])
        # t_ref = np.mean(frame_raw[80-self.REF_MEASURE_HEIGHT:80, 0:80])
        normalized = normalized - _mean_t_ref + self.REF_TEMP

        img_norm = (normalized - self.TEMP_FLOOR) * 255 / (self.TEMP_CEIL - self.TEMP_FLOOR)
        img_norm = np.clip(img_norm, 0, 255)
        img_norm = img_norm.astype('uint8')
        # img_preview = img_norm.copy()

        threshold_human_normalized = (self.THRESHOLD_HUMAN_TEMP - self.TEMP_FLOOR) * 255 / (
                self.TEMP_CEIL - self.TEMP_FLOOR)

        # test = np.min(img_norm)
        # print(test)

        # Resize de la imagen
        # img = cv2.resize(img_norm, (0,0), fx=5, fy=5)
        img = img_norm.copy()
        img[80 - self.REF_HEIGHT:, :] = 0
        if self.calibrating:
            # img[80 - self.REF_HEIGHT:, :] = 0
            img[80 - 1:, :] = 0
            # img[80 - self.REF_MEASURE_HEIGHT:, :] = 40

            img[self.y1_ref:self.y2_ref, self.x1_ref:self.x2_ref] = 40
            # print(y1_ref,y2_ref,x1_ref,x2_ref)

        else:
            img = img[0:80 - self.REF_HEIGHT, :]
            normalized = normalized[0:80 - self.REF_HEIGHT, :]

        # img_preview = img.copy()

        img_median = cv2.medianBlur(img, 3)
        # img_preview = img_median.copy()

        # Aca se puede hacer una deteccion de desenfoque de la camara.

        img_bilateral = cv2.bilateralFilter(img_median, 5, 3, 3)
        # img_preview = img_bilateral.copy()

        # Umbralizacion 
        ret, thresh = cv2.threshold(img_bilateral, threshold_human_normalized, 255, cv2.THRESH_BINARY)
        # img_preview = thresh.copy()

        custom_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))

        # Operadores morfologicos con ventana nxn
        morf = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, custom_kernel)
        # img_preview = morf.copy()

        # Deteccion de contornos
        contours, hierarchy = cv2.findContours(morf, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        # Mapa de calor
        img_large = cv2.applyColorMap(img, cv2.COLORMAP_PLASMA)
        img_large = cv2.resize(img_large, (0, 0), fx=self.OUTPUT_IMAGE_SCALE, fy=self.OUTPUT_IMAGE_SCALE,
                               interpolation=cv2.INTER_NEAREST)

        # Dibujar los contornos
        # cv2.drawContours(img_large, contours, -1, (0, 0, 255), thickness=1)

        main_contour = None
        main_contour_area = 0

        #  Se recorren todos los contornos para detectar los del rango de areas permitidas
        for i in range(len(contours)):
            area = cv2.contourArea(contours[i])
            if self.THRESHOLD_AREA_MIN < area < self.THRESHOLD_AREA_MAX:
                if area > main_contour_area:
                    main_contour_area = area
                    main_contour = contours[i]

        temperatures = None

        if main_contour is not None:
            large_contour = self.scale_contour(main_contour, self.OUTPUT_IMAGE_SCALE)
            cv2.drawContours(img_large, [large_contour], -1, (255, 255, 0), thickness=1)

            mask = np.zeros(normalized.shape, np.uint8)
            cv2.drawContours(mask, [main_contour], -1, 255, -1)

            x, y, w, h = cv2.boundingRect(large_contour)
            # norm = normalized.copy()

            temperatures_masked = ma.masked_array(normalized, ~mask)
            interest_data = temperatures_masked[temperatures_masked.mask == False]

            temperatures = {
                'temperature_min': round(np.ma.min(interest_data), 1),
                'temperature_mean': round(np.ma.mean(interest_data), 1),
                'temperature_median': round(np.ma.median(interest_data), 1),
                'temperature_max': round(np.ma.max(interest_data), 2),
                'temperature_p10': round(np.percentile(interest_data, 10), 1),
                'temperature_p20': round(np.percentile(interest_data, 20), 1),
                'temperature_p30': round(np.percentile(interest_data, 30), 1),
                'temperature_p40': round(np.percentile(interest_data, 40), 1),
                'temperature_p50': round(np.percentile(interest_data, 50), 1),
                'temperature_p60': round(np.percentile(interest_data, 60), 1),
                'temperature_p70': round(np.percentile(interest_data, 70), 1),
                'temperature_p80': round(np.percentile(interest_data, 80), 1),
                'temperature_p90': round(np.percentile(interest_data, 90), 1),
                'temperature_body': round(self.calculate_temp_human(np.percentile(interest_data, 80)), 1)
            }

            try:
                cv2.rectangle(img_large, (x, y), (x + w, y + h), (255, 255, 0), thickness=2)

                texto = "({:.1f})".format(temperatures.get('temperature_body'))
                cv2.putText(img_large, texto, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255))

                if self.calibrating:
                    raw_masked = ma.masked_array(frame_raw, ~mask)
                    raw_interest = raw_masked[raw_masked.mask == False]
                    raw_percentiles = [np.percentile(raw_interest, 70),
                                       np.percentile(raw_interest, 80),
                                       np.percentile(raw_interest, 90)]
                    ref_percentiles = [np.percentile(frame_raw[80 - self.REF_MEASURE_HEIGHT:80, 0:80], 70),
                                       np.percentile(frame_raw[80 - self.REF_MEASURE_HEIGHT:80, 0:80], 80),
                                       np.percentile(frame_raw[80 - self.REF_MEASURE_HEIGHT:80, 0:80], 90)]

                    texto_1 = "({:.1f},{:.1f},{:.1f})".format(temperatures.get('temperature_min'),
                                                              temperatures.get('temperature_mean'),
                                                              temperatures.get('temperature_max'))
                    # texto_2 = "({:.1f},{:.1f},{:.1f})".format(percentiles[0],percentiles[1],percentiles[2])
                    # texto_2 = "({:.1f},{:.1f},{:.1f})".format(ref_percentiles[0],ref_percentiles[1],ref_percentiles[2])
                    texto_2 = "({:.1f},{:.1f},{:.1f})".format(temperatures.get('temperature_p70'),
                                                              temperatures.get('temperature_p80'),
                                                              temperatures.get('temperature_p90'))
                    texto_3 = "({:.1f},{:.1f},{:.1f})".format(raw_percentiles[1], ref_percentiles[1],
                                                              raw_percentiles[1] - ref_percentiles[1])
                    cv2.putText(img_large, texto_1, (x, y + h + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255))
                    cv2.putText(img_large, texto_2, (x, y + h + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255))
                    cv2.putText(img_large, texto_3, (x, y + h + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255))
            except Exception as e:
                print(e)

        return img_large, temperatures
