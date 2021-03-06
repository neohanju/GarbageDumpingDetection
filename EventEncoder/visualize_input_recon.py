import numpy as np
import cv2
import os
import progressbar
import glob
import argparse
from random import shuffle

kOriginCoord = 0
kImageSize = 600

kLimbs = [[1, 2], [1, 5], [2, 3], [3, 4], [5, 6],
         [6, 7], [1, 8], [8, 9], [9, 10], [1, 11],
         [11, 12], [12, 13], [1, 0]]

parser = argparse.ArgumentParser(description='Visualizing input and reconstruction via video')
# model related ---------------------------------------------------------------
parser.add_argument('--input_path', type=str, default='', help="path for input data.")
parser.add_argument('--recon_path', type=str, default='', help="path for reconstructions.")
parser.add_argument('--save_path', type=str, default='', help="result video save path.")
parser.add_argument('--random_sample', type=int, help="number of random sampling")
options = parser.parse_args()
print(options)


def draw_keypoints(img, keypoints, confidences, color):
    xs = keypoints[0::2]
    ys = keypoints[1::2]
    for limb in kLimbs:
        if 0 == confidences[limb[0]] * confidences[limb[1]]:
            continue
        point_1 = (int(xs[limb[0]]), int(ys[limb[0]]))
        point_2 = (int(xs[limb[1]]), int(ys[limb[1]]))
        cv2.line(img, point_1, point_2, color, thickness=3)

    for ptIdx in range(len(xs)):
        if 0 == confidences[ptIdx]:
            continue
        center = (int(xs[ptIdx]), int(ys[ptIdx]))
        cv2.circle(img, center, 4, color=color, thickness=-1)

    return img


if __name__ == "__main__":

    sample_paths = glob.glob(os.path.join(options.input_path, "*.npy"))
    kHaveDisplay = "DISPLAY" in os.environ
    os.mkdir(options.save_path)

    if options.random_sample:
        shuffle(sample_paths)
        sample_paths = sample_paths[0:options.random_sample]

    for k in progressbar.progressbar(range(len(sample_paths))):

        inputFileName = os.path.basename(sample_paths[k]).split('.')[0]
        input_sample = np.load(sample_paths[k])
        recon_sample = np.load(os.path.join(options.recon_path, inputFileName + '-recon.npy'))

        # rescale and translation
        non_zero_input = np.array([val if val != 0 else kOriginCoord for val in input_sample.flatten()])
        non_zero_recon = np.array([val if val != 0 else kOriginCoord for val in recon_sample.flatten()])
        max_pos = np.amax(abs(non_zero_input - kOriginCoord))
        # only consider the range of original data, because the reconstructed one has outlier points
        pos_range = max_pos * 1.1
        input_sample_adjusted = 0.5 * kImageSize * ((input_sample - kOriginCoord) / max_pos + 1.0)
        recon_sample_adjusted = 0.5 * kImageSize * ((recon_sample - kOriginCoord) / max_pos + 1.0)

        # video writer
        fourcc = cv2.VideoWriter_fourcc('D', 'I', 'V', 'X')
        video_out = cv2.VideoWriter(os.path.join(options.save_path, inputFileName + '.avi'),
                                    fourcc, 30.0, (kImageSize, kImageSize))

        for i in range(input_sample.shape[0]):

            xs = input_sample[i, 0::2]
            ys = input_sample[i, 1::2]
            confidences = [1] * len(xs)
            for j in range(len(xs)):
                if 0 == xs[j] + ys[j] and j != 1:  # exclude the first neck point
                    confidences[j] = 0

            img = np.zeros((kImageSize, kImageSize, 3), np.uint8)
            img = draw_keypoints(img, input_sample_adjusted[i, :], confidences, (0, 0, 255))
            img = draw_keypoints(img, recon_sample_adjusted[i, :], confidences, (0, 255, 0))
            video_out.write(img)

            if kHaveDisplay:
                cv2.imshow('frame', img)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        video_out.release()

    if kHaveDisplay:
        cv2.destroyAllWindows()


# ()()
# ('')HAANJU.YOO
