#include <iostream>
#include <vector>

#include "opencv/cv.h"
#include "opencv/highgui.h"

using namespace std;
using namespace cv;

int main(int argc, char *argv[])
{
    // Create images of several image types.
    Mat img(50, 50, CV_8UC1, Scalar(0));
    Mat img_f(5, 5, CV_32FC1, Scalar(0));
    Mat img_2f(5, 5, CV_32FC2, Scalar(0));
    Mat img_3f(5, 5, CV_32FC3, Scalar(0));
    Mat img_4f(5, 5, CV_32FC4, Scalar(0));
    Mat img_u(5, 5, CV_USRTYPE1, Scalar(0));
    Mat img_3(500, 500, CV_8UC3, Scalar(0, 0, 0));
    Mat img_2(5, 5, CV_8UC2, Scalar(0, 0, 0));

    // Modify images.
    rectangle(img, Point(10, 10), Point(30, 30), Scalar(200), CV_FILLED);
    rectangle(img_f, Point(1, 1), Point(3, 3), Scalar(255), CV_FILLED);
    rectangle(img_3, Point(100, 100), Point(300, 300), Scalar(255, 0, 0), CV_FILLED);

    // Read image from file.
    Mat read_img = imread("gogh.jpg");
    Mat roi_img(read_img, Rect(50, 50, 100, 100));

    IplImage *iplImage = cvLoadImage("gogh.jpg");

    return 0;
}

