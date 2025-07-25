export interface Point3D {
    x: number;
    y: number;
    z: number;
}

export function angleBetween(p1: Point3D, p2: Point3D, p3: Point3D): number {
    const v1 = { x: p1.x - p2.x, y: p1.y - p2.y, z: p1.z - p2.z };
    const v2 = { x: p3.x - p2.x, y: p3.y - p2.y, z: p3.z - p2.z };
    const dot = v1.x * v2.x + v1.y * v2.y + v1.z * v2.z;
    const len1 = Math.sqrt(v1.x ** 2 + v1.y ** 2 + v1.z ** 2);
    const len2 = Math.sqrt(v2.x ** 2 + v2.y ** 2 + v2.z ** 2);
    return Math.acos(dot / (len1 * len2));
}

export function neckBackAngle(points: Point3D[]): number {
    const [shoulder, ear, hip] = points;
    return angleBetween(ear, shoulder, hip);
}

export function shoulderHipAngle(leftShoulder: Point3D, rightShoulder: Point3D, leftHip: Point3D, rightHip: Point3D): number {
    const midShoulder = {
        x: (leftShoulder.x + rightShoulder.x) / 2,
        y: (leftShoulder.y + rightShoulder.y) / 2,
        z: (leftShoulder.z + rightShoulder.z) / 2
    };
    const midHip = {
        x: (leftHip.x + rightHip.x) / 2,
        y: (leftHip.y + rightHip.y) / 2,
        z: (leftHip.z + rightHip.z) / 2
    };
    const vertical = { x: midShoulder.x, y: midShoulder.y - 1, z: midShoulder.z };
    return angleBetween(midHip, midShoulder, vertical);
}
