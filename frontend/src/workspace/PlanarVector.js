/**
 * A two-dimensional vector in the plane.
 * The vector is encoded with an origin Point and end Point.
 * @extends Array
 */
export default class PlanarVector {
  dot(vector) {
    return this[0] * vector[0] + this[1] * vector[1];
  }

  cross(vector) {
    return this[0] * vector[1] - this[1] * vector[0];
  }

  parallelTo(vector) {
    return this.cross(vector) === 0;
  }

  perpendicularTo(vector) {
    return this.dot(vector) === 0;
  }
}
